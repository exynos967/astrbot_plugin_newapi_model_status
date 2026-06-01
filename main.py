from __future__ import annotations

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

from .errors import NewApiRequestError, PluginConfigurationError, RemoteSelectionEmptyError
from .models import AVAILABLE_IMAGE_THEMES, PluginSettings
from .scheduler import PushJobScheduler
from .service import NewApiHealthReportService


@register(
    "newapi_model_status",
    "OpenAI",
    "查看并推送 NewAPI 模型健康度图卡",
    "0.1.0",
)
class NewApiModelStatusPlugin(Star):
    """NewAPI 模型健康度 AstrBot 插件。"""

    def __init__(self, context: Context, config=None) -> None:
        super().__init__(context, config)
        self.config = config if config is not None else {}
        self._scheduler = PushJobScheduler(
            context=context,
            star=self,
            settings_provider=self._get_settings,
            report_service_factory=self._build_service,
        )

    async def initialize(self) -> None:
        """初始化定时推送任务。"""
        await self._scheduler.initialize()

    async def terminate(self) -> None:
        """卸载时清理定时任务。"""
        await self._scheduler.terminate()

    @filter.command("模型情况")
    async def show_newapi_health(self, event: AstrMessageEvent, theme: str = ""):
        """查看当前 new_api_tools 已选模型的健康度图卡。"""
        service = self._build_service(self._get_settings())
        try:
            report = await service.build_report(self, theme_override=theme or None)
        except PluginConfigurationError as exc:
            yield event.plain_result(str(exc))
            return
        except RemoteSelectionEmptyError as exc:
            yield event.plain_result(str(exc))
            return
        except NewApiRequestError as exc:
            logger.warning(f"获取 NewAPI 模型健康度失败：{exc}")
            yield event.plain_result(f"获取模型健康度失败：{exc}")
            return
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"获取 NewAPI 模型健康度时出现未预期错误：{exc}")
            yield event.plain_result("获取模型健康度失败：出现未预期错误，请查看 AstrBot 日志。")
            return

        for page in report.pages:
            yield event.image_result(page.image_url)

    @filter.command("模型情况主题")
    async def show_theme_list(self, event: AstrMessageEvent):
        """显示可用图片主题列表。"""
        yield event.plain_result(
            "可用图片主题如下：\n"
            + "\n".join(f"- {item}" for item in AVAILABLE_IMAGE_THEMES)
            + "\n\n使用方式：/模型情况 openai\n"
            + "如果想继续跟随 new_api_tools 后台主题，请使用：/模型情况 follow_remote"
        )

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("模型情况会话")
    async def show_session_origin(self, event: AstrMessageEvent):
        """显示当前群号，方便配置固定推送目标。"""
        group_id = event.get_group_id()
        if not group_id:
            yield event.plain_result("当前不是群聊消息，固定推送目标列表现在需要直接填写 QQ 群号。")
            return
        yield event.plain_result(
            "当前群号如下，请直接填写到插件配置的固定推送目标列表中：\n"
            f"{group_id}"
        )

    def _get_settings(self) -> PluginSettings:
        return PluginSettings.from_config(self.config)

    def _build_service(self, settings: PluginSettings) -> NewApiHealthReportService:
        return NewApiHealthReportService(settings=settings)
