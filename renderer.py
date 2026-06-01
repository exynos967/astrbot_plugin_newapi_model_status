from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Protocol

from .models import (
    AVAILABLE_RENDER_THEMES,
    FOLLOW_REMOTE_THEME,
    DEFAULT_THEME,
    HealthSnapshot,
    ModelStatus,
)

logger = logging.getLogger(__name__)


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>NewAPI 模型健康度</title>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
        "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
      background: {{ palette.page_background }};
      color: {{ palette.text }};
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
      text-rendering: geometricPrecision;
    }
    .page {
      width: {{ page_width }}px;
      min-height: 720px;
      margin: 0 auto;
      padding: 40px;
      background: {{ palette.page_background }};
    }
    .hero {
      padding: 32px 36px;
      border-radius: 28px;
      background: {{ palette.hero_background }};
      border: 1px solid {{ palette.hero_border }};
      box-shadow: {{ palette.hero_shadow }};
      margin-bottom: 28px;
    }
    .hero-top {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 24px;
    }
    .title {
      font-size: 42px;
      font-weight: 700;
      line-height: 1.2;
      margin: 0;
      letter-spacing: -0.02em;
    }
    .subtitle {
      margin-top: 12px;
      font-size: 18px;
      color: {{ palette.muted_text }};
    }
    .summary-grid {
      margin-top: 24px;
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
    }
    .summary-card {
      padding: 18px 20px;
      border-radius: 18px;
      background: {{ palette.card_background }};
      border: 1px solid {{ palette.card_border }};
    }
    .summary-label {
      font-size: 15px;
      color: {{ palette.muted_text }};
      margin-bottom: 10px;
    }
    .summary-value {
      font-size: 28px;
      font-weight: 700;
    }
    .model-grid {
      display: grid;
      grid-template-columns: repeat({{ grid_columns }}, minmax(0, 1fr));
      gap: 22px;
    }
    .model-card {
      padding: 24px 26px;
      border-radius: 24px;
      background: {{ palette.card_background }};
      border: 1px solid {{ palette.card_border }};
      box-shadow: {{ palette.card_shadow }};
      overflow: hidden;
    }
    .model-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin-bottom: 18px;
    }
    .model-name {
      font-size: 24px;
      font-weight: 700;
      line-height: 1.3;
      max-width: 520px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .badge {
      padding: 7px 12px;
      border-radius: 999px;
      font-size: 14px;
      font-weight: 700;
      border: 1px solid transparent;
      white-space: nowrap;
    }
    .badge-green { color: #0f766e; background: rgba(16, 185, 129, 0.14); border-color: rgba(16, 185, 129, 0.28); }
    .badge-yellow { color: #b45309; background: rgba(245, 158, 11, 0.16); border-color: rgba(245, 158, 11, 0.28); }
    .badge-red { color: #be123c; background: rgba(244, 63, 94, 0.14); border-color: rgba(244, 63, 94, 0.28); }
    .stats {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }
    .stat {
      padding: 14px 16px;
      border-radius: 16px;
      background: {{ palette.stat_background }};
      border: 1px solid {{ palette.stat_border }};
    }
    .stat-label {
      font-size: 14px;
      color: {{ palette.muted_text }};
      margin-bottom: 10px;
    }
    .stat-value {
      font-size: 24px;
      font-weight: 700;
    }
    .timeline-title {
      font-size: 14px;
      color: {{ palette.muted_text }};
      margin-bottom: 12px;
    }
    .timeline {
      display: grid;
      grid-template-columns: repeat({{ slot_count }}, minmax(0, 1fr));
      gap: 4px;
      align-items: end;
      height: 84px;
    }
    .slot {
      width: 100%;
      border-radius: 9px;
      background: #d1d5db;
      min-height: 28px;
    }
    .slot-empty { background: {{ palette.empty_slot }}; }
    .slot-green { background: #10b981; }
    .slot-yellow { background: #f59e0b; }
    .slot-red { background: #f43f5e; }
    .legend {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 14px;
      gap: 12px;
      font-size: 14px;
      color: {{ palette.muted_text }};
    }
    .legend-items {
      display: flex;
      gap: 14px;
      align-items: center;
      flex-wrap: wrap;
    }
    .legend-item {
      display: flex;
      gap: 6px;
      align-items: center;
    }
    .legend-dot {
      width: 12px;
      height: 12px;
      border-radius: 999px;
    }
    .footer {
      margin-top: 26px;
      text-align: right;
      font-size: 14px;
      color: {{ palette.muted_text }};
    }
    .empty-state {
      padding: 80px 36px;
      text-align: center;
      border-radius: 28px;
      background: {{ palette.card_background }};
      border: 1px solid {{ palette.card_border }};
      box-shadow: {{ palette.card_shadow }};
    }
    .empty-title {
      margin: 0 0 14px;
      font-size: 32px;
      font-weight: 700;
    }
    .empty-text {
      font-size: 18px;
      line-height: 1.7;
      color: {{ palette.muted_text }};
      white-space: pre-line;
    }
  </style>
</head>
<body>
  <div class="page">
    <section class="hero">
      <div class="hero-top">
        <div>
          <h1 class="title">{{ title }}</h1>
          <div class="subtitle">{{ subtitle }}</div>
        </div>
        <div class="subtitle">第 {{ page_index }} / {{ page_total }} 页</div>
      </div>
      <div class="summary-grid">
        <div class="summary-card">
          <div class="summary-label">时间窗口</div>
          <div class="summary-value">{{ window_label }}</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">当前页模型数</div>
          <div class="summary-value">{{ visible_models }}</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">总模型数</div>
          <div class="summary-value">{{ total_models }}</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">数据来源</div>
          <div class="summary-value">{{ source_label }}</div>
        </div>
      </div>
    </section>

    {% if cards %}
    <section class="model-grid">
      {% for card in cards %}
      <article class="model-card">
        <div class="model-header">
          <div class="model-name">{{ card.display_name }}</div>
          <span class="badge badge-{{ card.status_class }}">{{ card.status_label }}</span>
        </div>
        <div class="stats">
          <div class="stat">
            <div class="stat-label">总请求</div>
            <div class="stat-value">{{ card.total_requests }}</div>
          </div>
          <div class="stat">
            <div class="stat-label">成功请求</div>
            <div class="stat-value">{{ card.success_count }}</div>
          </div>
          <div class="stat">
            <div class="stat-label">成功率</div>
            <div class="stat-value">{{ card.success_rate }}</div>
          </div>
        </div>
        <div class="timeline-title">{{ card.timeline_label }}</div>
        <div class="timeline">
          {% for slot in card.slots %}
          <div class="slot slot-{{ slot.css_class }}"></div>
          {% endfor %}
        </div>
        <div class="legend">
          <div>{{ card.model_name }}</div>
          <div>{{ card.slot_summary }}</div>
        </div>
      </article>
      {% endfor %}
    </section>
    {% else %}
    <section class="empty-state">
      <h2 class="empty-title">当前没有可展示的模型健康度数据</h2>
      <div class="empty-text">{{ empty_text }}</div>
    </section>
    {% endif %}

    <div class="footer">
      生成时间：{{ generated_at }} · 主题：{{ theme_name }}
    </div>
  </div>
</body>
</html>
"""


BASE_DAY = {
    "page_background": "linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%)",
    "hero_background": "rgba(255, 255, 255, 0.92)",
    "hero_border": "rgba(148, 163, 184, 0.22)",
    "hero_shadow": "0 16px 40px rgba(15, 23, 42, 0.08)",
    "card_background": "rgba(255, 255, 255, 0.95)",
    "card_border": "rgba(148, 163, 184, 0.20)",
    "card_shadow": "0 10px 28px rgba(15, 23, 42, 0.06)",
    "stat_background": "rgba(248, 250, 252, 0.95)",
    "stat_border": "rgba(203, 213, 225, 0.7)",
    "text": "#0f172a",
    "muted_text": "#64748b",
    "empty_slot": "#e2e8f0",
}

BASE_NIGHT = {
    "page_background": "linear-gradient(180deg, #020617 0%, #0f172a 100%)",
    "hero_background": "rgba(15, 23, 42, 0.88)",
    "hero_border": "rgba(148, 163, 184, 0.18)",
    "hero_shadow": "0 18px 42px rgba(2, 6, 23, 0.35)",
    "card_background": "rgba(15, 23, 42, 0.9)",
    "card_border": "rgba(71, 85, 105, 0.6)",
    "card_shadow": "0 10px 24px rgba(2, 6, 23, 0.22)",
    "stat_background": "rgba(15, 23, 42, 0.92)",
    "stat_border": "rgba(71, 85, 105, 0.8)",
    "text": "#e2e8f0",
    "muted_text": "#94a3b8",
    "empty_slot": "#334155",
}

PALETTES = {
    "daylight": BASE_DAY,
    "obsidian": BASE_NIGHT,
    "minimal": {
        **BASE_DAY,
        "page_background": "#ffffff",
        "hero_background": "#ffffff",
        "hero_border": "rgba(15, 23, 42, 0.08)",
        "hero_shadow": "0 4px 20px rgba(15, 23, 42, 0.04)",
        "card_background": "#ffffff",
        "card_border": "rgba(15, 23, 42, 0.08)",
        "card_shadow": "none",
        "stat_background": "#fafafa",
        "stat_border": "rgba(15, 23, 42, 0.08)",
        "muted_text": "#6b7280",
        "empty_slot": "#e5e7eb",
    },
    "neon": {
        **BASE_NIGHT,
        "page_background": "radial-gradient(circle at top, #172554 0%, #020617 45%, #000000 100%)",
        "hero_background": "linear-gradient(135deg, rgba(8, 47, 73, 0.9), rgba(91, 33, 182, 0.88))",
        "hero_border": "rgba(34, 211, 238, 0.35)",
        "hero_shadow": "0 0 40px rgba(34, 211, 238, 0.18)",
        "card_background": "rgba(3, 7, 18, 0.92)",
        "card_border": "rgba(34, 211, 238, 0.20)",
        "card_shadow": "0 0 28px rgba(56, 189, 248, 0.12)",
        "stat_background": "rgba(8, 47, 73, 0.35)",
        "stat_border": "rgba(34, 211, 238, 0.18)",
        "text": "#e0f2fe",
        "muted_text": "#7dd3fc",
        "empty_slot": "#164e63",
    },
    "forest": {
        **BASE_NIGHT,
        "page_background": "linear-gradient(180deg, #022c22 0%, #052e16 55%, #020617 100%)",
        "hero_background": "linear-gradient(135deg, rgba(6, 78, 59, 0.92), rgba(20, 83, 45, 0.92))",
        "hero_border": "rgba(74, 222, 128, 0.18)",
        "card_background": "rgba(6, 46, 26, 0.88)",
        "card_border": "rgba(74, 222, 128, 0.16)",
        "stat_background": "rgba(21, 128, 61, 0.18)",
        "stat_border": "rgba(74, 222, 128, 0.14)",
        "text": "#ecfdf5",
        "muted_text": "#86efac",
        "empty_slot": "#166534",
    },
    "ocean": {
        **BASE_NIGHT,
        "page_background": "linear-gradient(180deg, #082f49 0%, #0f172a 60%, #020617 100%)",
        "hero_background": "linear-gradient(135deg, rgba(14, 116, 144, 0.92), rgba(30, 64, 175, 0.9))",
        "hero_border": "rgba(125, 211, 252, 0.18)",
        "card_background": "rgba(8, 47, 73, 0.68)",
        "card_border": "rgba(125, 211, 252, 0.16)",
        "stat_background": "rgba(14, 116, 144, 0.16)",
        "stat_border": "rgba(125, 211, 252, 0.14)",
        "text": "#e0f2fe",
        "muted_text": "#93c5fd",
        "empty_slot": "#1d4ed8",
    },
    "terminal": {
        **BASE_NIGHT,
        "page_background": "#000000",
        "hero_background": "rgba(0, 0, 0, 0.96)",
        "hero_border": "rgba(34, 197, 94, 0.4)",
        "hero_shadow": "0 0 28px rgba(34, 197, 94, 0.16)",
        "card_background": "rgba(1, 15, 7, 0.96)",
        "card_border": "rgba(34, 197, 94, 0.28)",
        "card_shadow": "0 0 20px rgba(34, 197, 94, 0.12)",
        "stat_background": "rgba(5, 46, 22, 0.95)",
        "stat_border": "rgba(34, 197, 94, 0.22)",
        "text": "#bbf7d0",
        "muted_text": "#86efac",
        "empty_slot": "#14532d",
    },
    "cupertino": {
        **BASE_DAY,
        "page_background": "linear-gradient(180deg, #f5f5f7 0%, #eef2ff 100%)",
        "hero_background": "rgba(255, 255, 255, 0.78)",
        "hero_border": "rgba(148, 163, 184, 0.14)",
        "hero_shadow": "0 16px 42px rgba(148, 163, 184, 0.12)",
        "card_background": "rgba(255, 255, 255, 0.76)",
        "card_border": "rgba(148, 163, 184, 0.14)",
        "card_shadow": "0 14px 32px rgba(148, 163, 184, 0.12)",
        "stat_background": "rgba(248, 250, 252, 0.86)",
        "stat_border": "rgba(203, 213, 225, 0.55)",
        "muted_text": "#6b7280",
        "empty_slot": "#cbd5e1",
    },
    "material": {
        **BASE_DAY,
        "page_background": "linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%)",
        "hero_background": "linear-gradient(135deg, rgba(255,255,255,0.96), rgba(240,244,248,0.96))",
        "hero_border": "rgba(59, 130, 246, 0.14)",
        "hero_shadow": "0 14px 30px rgba(59, 130, 246, 0.08)",
        "card_background": "#ffffff",
        "card_border": "rgba(148, 163, 184, 0.18)",
        "card_shadow": "0 10px 24px rgba(15, 23, 42, 0.08)",
        "stat_background": "rgba(239, 246, 255, 0.98)",
        "stat_border": "rgba(147, 197, 253, 0.4)",
        "empty_slot": "#bfdbfe",
    },
    "openai": {
        **BASE_NIGHT,
        "page_background": "linear-gradient(180deg, #202123 0%, #343541 100%)",
        "hero_background": "linear-gradient(135deg, rgba(52, 53, 65, 0.98), rgba(32, 33, 35, 0.96))",
        "hero_border": "rgba(255, 255, 255, 0.06)",
        "card_background": "rgba(52, 53, 65, 0.92)",
        "card_border": "rgba(255, 255, 255, 0.08)",
        "stat_background": "rgba(64, 65, 79, 0.92)",
        "stat_border": "rgba(255, 255, 255, 0.07)",
        "text": "#ececf1",
        "muted_text": "#c5c5d2",
        "empty_slot": "#4b5563",
    },
    "anthropic": {
        **BASE_DAY,
        "page_background": "linear-gradient(180deg, #f5f1e8 0%, #efe6d6 100%)",
        "hero_background": "rgba(244, 241, 234, 0.98)",
        "hero_border": "rgba(146, 115, 85, 0.14)",
        "card_background": "rgba(255, 251, 245, 0.96)",
        "card_border": "rgba(146, 115, 85, 0.14)",
        "stat_background": "rgba(250, 245, 236, 0.94)",
        "stat_border": "rgba(180, 151, 122, 0.16)",
        "text": "#3f2f1d",
        "muted_text": "#7c5f3d",
        "empty_slot": "#d6c3a5",
    },
    "vercel": {
        **BASE_NIGHT,
        "page_background": "#000000",
        "hero_background": "linear-gradient(135deg, rgba(10,10,10,0.98), rgba(24,24,27,0.95))",
        "hero_border": "rgba(255,255,255,0.08)",
        "card_background": "rgba(10,10,10,0.94)",
        "card_border": "rgba(255,255,255,0.08)",
        "stat_background": "rgba(24,24,27,0.94)",
        "stat_border": "rgba(255,255,255,0.08)",
        "text": "#fafafa",
        "muted_text": "#a1a1aa",
        "empty_slot": "#3f3f46",
    },
    "linear": {
        **BASE_NIGHT,
        "page_background": "radial-gradient(circle at top, #1f2440 0%, #0f1015 42%, #09090b 100%)",
        "hero_background": "linear-gradient(135deg, rgba(31,36,64,0.96), rgba(15,16,21,0.95))",
        "hero_border": "rgba(167, 139, 250, 0.16)",
        "card_background": "rgba(17, 24, 39, 0.92)",
        "card_border": "rgba(167, 139, 250, 0.14)",
        "card_shadow": "0 12px 30px rgba(99, 102, 241, 0.12)",
        "stat_background": "rgba(30, 41, 59, 0.86)",
        "stat_border": "rgba(167, 139, 250, 0.14)",
        "text": "#f8fafc",
        "muted_text": "#c4b5fd",
        "empty_slot": "#3730a3",
    },
    "stripe": {
        **BASE_DAY,
        "page_background": "linear-gradient(180deg, #fdfbff 0%, #eef4ff 100%)",
        "hero_background": "linear-gradient(135deg, rgba(255,255,255,0.98), rgba(238,244,255,0.98))",
        "hero_border": "rgba(99, 102, 241, 0.12)",
        "hero_shadow": "0 18px 40px rgba(99, 102, 241, 0.10)",
        "card_background": "rgba(255,255,255,0.98)",
        "card_border": "rgba(99, 102, 241, 0.10)",
        "card_shadow": "0 12px 30px rgba(99, 102, 241, 0.08)",
        "stat_background": "rgba(245, 243, 255, 0.96)",
        "stat_border": "rgba(129, 140, 248, 0.16)",
        "muted_text": "#6366f1",
        "empty_slot": "#c7d2fe",
    },
    "github": {
        **BASE_NIGHT,
        "page_background": "linear-gradient(180deg, #0d1117 0%, #161b22 100%)",
        "hero_background": "rgba(22, 27, 34, 0.98)",
        "hero_border": "rgba(110, 118, 129, 0.22)",
        "card_background": "rgba(22, 27, 34, 0.96)",
        "card_border": "rgba(110, 118, 129, 0.18)",
        "stat_background": "rgba(13, 17, 23, 0.96)",
        "stat_border": "rgba(110, 118, 129, 0.16)",
        "text": "#e6edf3",
        "muted_text": "#8b949e",
        "empty_slot": "#30363d",
    },
    "discord": {
        **BASE_NIGHT,
        "page_background": "linear-gradient(180deg, #313338 0%, #1e1f22 100%)",
        "hero_background": "linear-gradient(135deg, rgba(88, 101, 242, 0.25), rgba(49, 51, 56, 0.96))",
        "hero_border": "rgba(88, 101, 242, 0.22)",
        "card_background": "rgba(43, 45, 49, 0.96)",
        "card_border": "rgba(88, 101, 242, 0.18)",
        "stat_background": "rgba(49, 51, 56, 0.96)",
        "stat_border": "rgba(88, 101, 242, 0.16)",
        "text": "#f2f3f5",
        "muted_text": "#b5bac1",
        "empty_slot": "#4e5058",
    },
    "tesla": {
        **BASE_NIGHT,
        "page_background": "linear-gradient(180deg, #000000 0%, #111111 100%)",
        "hero_background": "linear-gradient(135deg, rgba(127,29,29,0.92), rgba(17,17,17,0.96))",
        "hero_border": "rgba(239, 68, 68, 0.18)",
        "hero_shadow": "0 18px 42px rgba(127,29,29,0.18)",
        "card_background": "rgba(12, 10, 9, 0.96)",
        "card_border": "rgba(239, 68, 68, 0.16)",
        "stat_background": "rgba(28, 25, 23, 0.96)",
        "stat_border": "rgba(248, 113, 113, 0.14)",
        "text": "#fafaf9",
        "muted_text": "#fca5a5",
        "empty_slot": "#7f1d1d",
    },
}

TIME_WINDOW_LABELS = {
    "1h": "1 小时",
    "6h": "6 小时",
    "12h": "12 小时",
    "24h": "24 小时",
}

STATUS_LABELS = {
    "green": "正常",
    "yellow": "警告",
    "red": "异常",
}


class HtmlRenderable(Protocol):
    async def html_render(
        self,
        tmpl: str,
        data: dict,
        return_url: bool = True,
        options: dict | None = None,
    ) -> str: ...

    async def text_to_image(self, text: str, return_url: bool = True) -> str: ...


@dataclass(frozen=True)
class RenderedPage:
    image_url: str
    page_index: int
    page_total: int


class HealthReportRenderer:
    """负责将健康度数据渲染为图片。"""

    screenshot_options = {
        "type": "png",
        "full_page": True,
        "animations": "disabled",
        "caret": "hide",
        "scale": "device",
        "timeout": 60000,
    }

    async def render_pages(
        self,
        star: HtmlRenderable,
        snapshot: HealthSnapshot,
        render_theme: str = FOLLOW_REMOTE_THEME,
    ) -> list[RenderedPage]:
        chunks = [list(snapshot.model_statuses)]
        page_total = 1
        resolved_theme = self._resolve_theme(render_theme, snapshot.remote_config.theme)
        palette = self._resolve_palette(resolved_theme)
        theme_name = resolved_theme
        title = snapshot.remote_config.site_title or "NewAPI 模型健康度"
        subtitle = (
            "复用 new_api_tools 公开 embed 配置"
            if snapshot.remote_config.site_title
            else "当前图卡由 AstrBot 插件生成"
        )
        generated_at = snapshot.fetched_at.strftime("%Y-%m-%d %H:%M:%S %Z")

        rendered_pages: list[RenderedPage] = []
        for index, chunk in enumerate(chunks, start=1):
            data = {
                "palette": palette,
                "title": title,
                "subtitle": subtitle,
                "page_index": index,
                "page_total": page_total,
                "page_width": self._resolve_page_width(len(chunk)),
                "grid_columns": self._resolve_grid_columns(len(chunk)),
                "window_label": TIME_WINDOW_LABELS.get(
                    snapshot.remote_config.time_window,
                    snapshot.remote_config.time_window,
                ),
                "visible_models": len(chunk),
                "total_models": len(snapshot.model_statuses),
                "source_label": snapshot.source_label,
                "theme_name": theme_name,
                "generated_at": generated_at,
                "cards": [self._build_card(item) for item in chunk],
                "empty_text": "已成功访问 new_api_tools，但当前选中的模型暂无最近日志数据。",
                "slot_count": max(1, len(chunk[0].slot_data) if chunk else 24),
            }
            try:
                image_url = await star.html_render(
                    HTML_TEMPLATE,
                    data,
                    options=self.screenshot_options,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("HTML 渲染失败，回退到文本转图片。原因：%s", exc)
                fallback_text = self._build_fallback_markdown(
                    snapshot=snapshot,
                    theme_name=theme_name,
                    title=title,
                )
                image_url = await star.text_to_image(fallback_text)
            rendered_pages.append(
                RenderedPage(image_url=image_url, page_index=index, page_total=page_total)
            )

        return rendered_pages

    def _resolve_palette(self, theme_id: str) -> dict[str, str]:
        return PALETTES.get(theme_id, PALETTES[DEFAULT_THEME])

    def _resolve_theme(self, render_theme: str, remote_theme: str) -> str:
        if render_theme == FOLLOW_REMOTE_THEME:
            if remote_theme in AVAILABLE_RENDER_THEMES:
                return remote_theme
            return DEFAULT_THEME
        if render_theme in AVAILABLE_RENDER_THEMES:
            return render_theme
        return DEFAULT_THEME

    def _resolve_page_width(self, model_count: int) -> int:
        if model_count <= 1:
            return 1640
        if model_count <= 6:
            return 1980
        if model_count <= 12:
            return 2760
        return 3440

    def _resolve_grid_columns(self, model_count: int) -> int:
        if model_count <= 1:
            return 1
        if model_count <= 6:
            return 2
        if model_count <= 12:
            return 3
        return 4

    def _build_card(self, model_status: ModelStatus) -> dict:
        slots = []
        for slot in model_status.slot_data:
            if slot.total_requests <= 0:
                css_class = "empty"
            else:
                css_class = slot.status if slot.status in STATUS_LABELS else "green"
            slots.append({"css_class": css_class})
        return {
            "model_name": model_status.model_name,
            "display_name": model_status.display_name,
            "total_requests": model_status.total_requests,
            "success_count": model_status.success_count,
            "success_rate": f"{model_status.success_rate:.2f}%",
            "status_class": (
                model_status.current_status
                if model_status.current_status in STATUS_LABELS
                else "green"
            ),
            "status_label": STATUS_LABELS.get(model_status.current_status, "正常"),
            "timeline_label": "时间槽趋势（绿=正常，黄=警告，红=异常，灰=无请求）",
            "slots": slots,
            "slot_summary": f"{len(model_status.slot_data)} 个时间槽",
        }

    def _build_fallback_markdown(
        self,
        snapshot: HealthSnapshot,
        theme_name: str,
        title: str,
    ) -> str:
        lines = [
            f"# {title}",
            "",
            f"- 时间窗口：{TIME_WINDOW_LABELS.get(snapshot.remote_config.time_window, snapshot.remote_config.time_window)}",
            f"- 图片主题：{theme_name}",
            f"- 模型数量：{len(snapshot.model_statuses)}",
            f"- 数据来源：{snapshot.source_label}",
            f"- 生成时间：{snapshot.fetched_at.strftime('%Y-%m-%d %H:%M:%S %Z')}",
            "",
        ]
        if not snapshot.model_statuses:
            lines.append("当前没有可展示的模型健康度数据。")
            return "\n".join(lines)

        for status in snapshot.model_statuses:
            lines.extend(
                [
                    f"## {status.display_name}",
                    f"- 状态：{STATUS_LABELS.get(status.current_status, '正常')}",
                    f"- 总请求：{status.total_requests}",
                    f"- 成功请求：{status.success_count}",
                    f"- 成功率：{status.success_rate:.2f}%",
                    f"- 时间槽：{self._build_slot_trend(status)}",
                    "",
                ]
            )
        return "\n".join(lines)

    def _build_slot_trend(self, model_status: ModelStatus) -> str:
        trend_chars: list[str] = []
        for slot in model_status.slot_data:
            if slot.total_requests <= 0:
                trend_chars.append("·")
            elif slot.status == "green":
                trend_chars.append("🟩")
            elif slot.status == "yellow":
                trend_chars.append("🟨")
            else:
                trend_chars.append("🟥")
        return "".join(trend_chars) or "无"
