from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

from .errors import NewApiRequestError, RemoteSelectionEmptyError
from .models import HealthSnapshot, ModelStatus, PluginSettings, RemoteConfig


@dataclass(frozen=True)
class EmbedRouteCandidate:
    source_label: str
    config_path: str
    batch_path: str


EMBED_ROUTE_CANDIDATES = (
    EmbedRouteCandidate(
        source_label="python-embed",
        config_path="/api/model-status/embed/config/selected",
        batch_path="/api/model-status/embed/status/batch",
    ),
    EmbedRouteCandidate(
        source_label="go-compat-embed",
        config_path="/api/embed/model-status/config/selected",
        batch_path="/api/embed/model-status/status/batch",
    ),
)


class NewApiModelStatusClient:
    """封装 new_api_tools 公开 embed 接口。"""

    def __init__(self, settings: PluginSettings) -> None:
        self.settings = settings

    async def fetch_snapshot(self) -> HealthSnapshot:
        self.settings.require_base_url()
        candidate_errors: list[str] = []

        async with httpx.AsyncClient(
            timeout=self.settings.request_timeout_seconds,
            verify=self.settings.verify_ssl,
            follow_redirects=True,
        ) as client:
            for candidate in EMBED_ROUTE_CANDIDATES:
                try:
                    remote_config = await self._fetch_remote_config(client, candidate)
                    if not remote_config.selected_models:
                        raise RemoteSelectionEmptyError(
                            "new_api_tools 当前未配置 selected models，请先到后台的模型健康度页面选择模型。"
                        )
                    model_statuses = await self._fetch_model_statuses(
                        client=client,
                        candidate=candidate,
                        remote_config=remote_config,
                    )
                    return HealthSnapshot(
                        remote_config=remote_config,
                        model_statuses=model_statuses,
                        fetched_at=datetime.now().astimezone(),
                        source_label=candidate.source_label,
                    )
                except RemoteSelectionEmptyError:
                    raise
                except NewApiRequestError as exc:
                    candidate_errors.append(str(exc))

        joined_errors = " | ".join(candidate_errors) if candidate_errors else "未获得可用路由"
        raise NewApiRequestError(
            f"无法从 new_api_tools 获取模型健康度数据：{joined_errors}"
        )

    async def _fetch_remote_config(
        self,
        client: httpx.AsyncClient,
        candidate: EmbedRouteCandidate,
    ) -> RemoteConfig:
        payload = await self._request_json(client, "GET", candidate.config_path)
        return RemoteConfig.from_dict(payload)

    async def _fetch_model_statuses(
        self,
        client: httpx.AsyncClient,
        candidate: EmbedRouteCandidate,
        remote_config: RemoteConfig,
    ) -> tuple[ModelStatus, ...]:
        payload = await self._request_json(
            client=client,
            method="POST",
            path=f"{candidate.batch_path}?window={remote_config.time_window}",
            json=list(remote_config.selected_models),
        )
        raw_items = payload.get("data") or []
        if not isinstance(raw_items, list):
            raise NewApiRequestError("模型健康度接口返回格式不正确：data 不是列表。")
        return tuple(
            ModelStatus.from_dict(item)
            for item in raw_items
            if isinstance(item, dict)
        )

    async def _request_json(
        self,
        client: httpx.AsyncClient,
        method: str,
        path: str,
        json: Any | None = None,
    ) -> dict[str, Any]:
        url = self._build_url(path)
        try:
            response = await client.request(method=method, url=url, json=json)
        except httpx.TimeoutException as exc:
            raise NewApiRequestError(f"{path} 请求超时。") from exc
        except httpx.HTTPError as exc:
            raise NewApiRequestError(f"{path} 请求失败：{exc}") from exc

        if response.status_code in {404, 405}:
            raise NewApiRequestError(f"{path} 不存在或方法不匹配（{response.status_code}）。")
        if response.status_code >= 400:
            body = response.text.strip().replace("\n", " ")
            raise NewApiRequestError(
                f"{path} 返回 HTTP {response.status_code}：{body[:180]}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise NewApiRequestError(f"{path} 返回了无法解析的 JSON。") from exc

        if not isinstance(payload, dict):
            raise NewApiRequestError(f"{path} 返回格式不正确。")

        if payload.get("success") is False:
            message = payload.get("message") or payload.get("error") or "接口返回 success=false"
            raise NewApiRequestError(f"{path} 返回失败：{message}")

        return payload

    def _build_url(self, path: str) -> str:
        base_url = self.settings.require_base_url()
        return f"{base_url}{path}" if path.startswith("/") else f"{base_url}/{path}"
