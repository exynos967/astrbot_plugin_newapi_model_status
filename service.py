from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .client import NewApiModelStatusClient
from .models import HealthSnapshot, PluginSettings
from .renderer import HealthReportRenderer, RenderedPage


class HtmlRenderable(Protocol):
    async def html_render(
        self,
        tmpl: str,
        data: dict,
        return_url: bool = True,
        options: dict | None = None,
    ) -> str: ...


@dataclass(frozen=True)
class RenderedHealthReport:
    snapshot: HealthSnapshot
    pages: tuple[RenderedPage, ...]


class NewApiHealthReportService:
    """组合客户端与渲染器，输出最终图卡。"""

    def __init__(
        self,
        settings: PluginSettings,
        client: NewApiModelStatusClient | None = None,
        renderer: HealthReportRenderer | None = None,
    ) -> None:
        self.settings = settings
        self.client = client or NewApiModelStatusClient(settings)
        self.renderer = renderer or HealthReportRenderer()

    async def build_report(
        self,
        star: HtmlRenderable,
        theme_override: str | None = None,
    ) -> RenderedHealthReport:
        snapshot = await self.client.fetch_snapshot()
        pages = await self.renderer.render_pages(
            star=star,
            snapshot=snapshot,
            render_theme=self.settings.resolve_render_theme(theme_override),
        )
        return RenderedHealthReport(snapshot=snapshot, pages=tuple(pages))
