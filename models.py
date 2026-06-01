from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from .errors import PluginConfigurationError

DEFAULT_THEME = "daylight"
FOLLOW_REMOTE_THEME = "follow_remote"
DEFAULT_TIME_WINDOW = "24h"
DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_PUSH_INTERVAL_MINUTES = 60
SUPPORTED_PUSH_INTERVALS = (15, 30, 60, 120, 180, 360, 720, 1440)
VALID_TIME_WINDOWS = {"1h", "6h", "12h", "24h"}
AVAILABLE_RENDER_THEMES = (
    "daylight",
    "obsidian",
    "minimal",
    "neon",
    "forest",
    "ocean",
    "terminal",
    "cupertino",
    "material",
    "openai",
    "anthropic",
    "vercel",
    "linear",
    "stripe",
    "github",
    "discord",
    "tesla",
)
AVAILABLE_IMAGE_THEMES = (FOLLOW_REMOTE_THEME, *AVAILABLE_RENDER_THEMES)
THEME_DISPLAY_NAMES = {
    FOLLOW_REMOTE_THEME: "follow_remote（跟随远端）",
    "daylight": "daylight（日光）",
    "obsidian": "obsidian（黑曜石）",
    "minimal": "minimal（极简）",
    "neon": "neon（霓虹）",
    "forest": "forest（森林）",
    "ocean": "ocean（海洋）",
    "terminal": "terminal（终端）",
    "cupertino": "cupertino（Apple）",
    "material": "material（Google）",
    "openai": "openai（OpenAI）",
    "anthropic": "anthropic（Claude）",
    "vercel": "vercel（Vercel）",
    "linear": "linear（Linear）",
    "stripe": "stripe（Stripe）",
    "github": "github（GitHub）",
    "discord": "discord（Discord）",
    "tesla": "tesla（Tesla）",
}


def _to_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class PushTarget:
    name: str
    group_id: str
    enabled: bool = True

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PushTarget | None":
        group_id = str(data.get("group_id") or "").strip()
        if not group_id:
            legacy_session = str(data.get("unified_msg_origin") or "").strip()
            if legacy_session.startswith("aiocqhttp:group:"):
                group_id = legacy_session.split(":", 2)[2].strip()
        if not group_id:
            return None
        name = str(data.get("name") or group_id).strip()
        enabled = _to_bool(data.get("enabled"), True)
        return cls(name=name, group_id=group_id, enabled=enabled)


@dataclass(frozen=True)
class PluginSettings:
    base_url: str
    request_timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    verify_ssl: bool = True
    image_theme: str = FOLLOW_REMOTE_THEME
    push_enabled: bool = False
    push_interval_minutes: int = DEFAULT_PUSH_INTERVAL_MINUTES
    push_targets: tuple[PushTarget, ...] = ()

    @classmethod
    def from_config(cls, config: Mapping[str, Any] | None) -> "PluginSettings":
        raw_config = config or {}
        base_url = str(raw_config.get("new_api_base_url") or "").strip().rstrip("/")
        request_timeout_seconds = max(
            3.0,
            _to_float(raw_config.get("request_timeout_seconds"), DEFAULT_TIMEOUT_SECONDS),
        )
        verify_ssl = _to_bool(raw_config.get("verify_ssl"), True)
        image_theme = str(raw_config.get("image_theme") or FOLLOW_REMOTE_THEME).strip()
        if image_theme not in AVAILABLE_IMAGE_THEMES:
            image_theme = FOLLOW_REMOTE_THEME
        push_enabled = _to_bool(raw_config.get("push_enabled"), False)
        push_interval_minutes = _to_int(
            raw_config.get("push_interval_minutes"),
            DEFAULT_PUSH_INTERVAL_MINUTES,
        )
        if push_interval_minutes not in SUPPORTED_PUSH_INTERVALS:
            push_interval_minutes = DEFAULT_PUSH_INTERVAL_MINUTES

        raw_targets = raw_config.get("push_targets") or []
        targets: list[PushTarget] = []
        for item in raw_targets:
            if not isinstance(item, Mapping):
                continue
            parsed = PushTarget.from_dict(item)
            if parsed:
                targets.append(parsed)

        return cls(
            base_url=base_url,
            request_timeout_seconds=request_timeout_seconds,
            verify_ssl=verify_ssl,
            image_theme=image_theme,
            push_enabled=push_enabled,
            push_interval_minutes=push_interval_minutes,
            push_targets=tuple(targets),
        )

    def require_base_url(self) -> str:
        if not self.base_url:
            raise PluginConfigurationError(
                "请先在插件配置中填写 new_api_tools 的地址（new_api_base_url）。"
            )
        return self.base_url

    @property
    def enabled_targets(self) -> tuple[PushTarget, ...]:
        return tuple(target for target in self.push_targets if target.enabled)

    def resolve_render_theme(self, theme_override: str | None = None) -> str:
        candidate = str(theme_override or self.image_theme or FOLLOW_REMOTE_THEME).strip()
        if not candidate:
            return FOLLOW_REMOTE_THEME
        if candidate not in AVAILABLE_IMAGE_THEMES:
            raise PluginConfigurationError(
                "无效的图片主题。可用主题："
                + ", ".join(AVAILABLE_IMAGE_THEMES)
            )
        return candidate


@dataclass(frozen=True)
class SlotStatus:
    slot: int
    start_time: int
    end_time: int
    total_requests: int
    success_count: int
    success_rate: float
    status: str

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SlotStatus":
        return cls(
            slot=_to_int(data.get("slot"), 0),
            start_time=_to_int(data.get("start_time"), 0),
            end_time=_to_int(data.get("end_time"), 0),
            total_requests=max(0, _to_int(data.get("total_requests"), 0)),
            success_count=max(0, _to_int(data.get("success_count"), 0)),
            success_rate=max(0.0, min(100.0, _to_float(data.get("success_rate"), 0.0))),
            status=str(data.get("status") or "green"),
        )


@dataclass(frozen=True)
class ModelStatus:
    model_name: str
    display_name: str
    time_window: str
    total_requests: int
    success_count: int
    success_rate: float
    current_status: str
    slot_data: tuple[SlotStatus, ...]

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ModelStatus":
        slot_items = data.get("slot_data") or []
        slot_data = tuple(
            SlotStatus.from_dict(item)
            for item in slot_items
            if isinstance(item, Mapping)
        )
        model_name = str(data.get("model_name") or "").strip()
        display_name = str(data.get("display_name") or model_name).strip() or model_name
        time_window = str(data.get("time_window") or DEFAULT_TIME_WINDOW)
        if time_window not in VALID_TIME_WINDOWS:
            time_window = DEFAULT_TIME_WINDOW
        return cls(
            model_name=model_name,
            display_name=display_name,
            time_window=time_window,
            total_requests=max(0, _to_int(data.get("total_requests"), 0)),
            success_count=max(0, _to_int(data.get("success_count"), 0)),
            success_rate=max(0.0, min(100.0, _to_float(data.get("success_rate"), 0.0))),
            current_status=str(data.get("current_status") or "green"),
            slot_data=slot_data,
        )


@dataclass(frozen=True)
class RemoteConfig:
    selected_models: tuple[str, ...]
    time_window: str = DEFAULT_TIME_WINDOW
    theme: str = DEFAULT_THEME
    site_title: str = ""

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RemoteConfig":
        raw_selected_models = data.get("data")
        if not isinstance(raw_selected_models, list):
            raw_selected_models = []
        selected_models = tuple(
            str(item).strip()
            for item in raw_selected_models
            if str(item).strip()
        )
        time_window = str(data.get("time_window") or DEFAULT_TIME_WINDOW)
        if time_window not in VALID_TIME_WINDOWS:
            time_window = DEFAULT_TIME_WINDOW
        theme = str(data.get("theme") or DEFAULT_THEME).strip() or DEFAULT_THEME
        site_title = str(data.get("site_title") or "").strip()
        return cls(
            selected_models=selected_models,
            time_window=time_window,
            theme=theme,
            site_title=site_title,
        )


@dataclass(frozen=True)
class HealthSnapshot:
    remote_config: RemoteConfig
    model_statuses: tuple[ModelStatus, ...]
    fetched_at: datetime
    source_label: str
