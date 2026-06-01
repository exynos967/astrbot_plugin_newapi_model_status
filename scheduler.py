from __future__ import annotations

import asyncio
from typing import Any, Callable

from astrbot.api import logger
from astrbot.api.event import MessageChain
from astrbot.api.star import Context, Star
from astrbot.core.platform.message_session import MessageSesion
from astrbot.core.platform.message_type import MessageType

from .errors import NewApiRequestError, PluginConfigurationError, RemoteSelectionEmptyError
from .models import PluginSettings
from .service import NewApiHealthReportService

PLUGIN_JOB_KEY = "astrbot_plugin_newapi_model_status_push"
PLUGIN_JOB_NAME = "NewAPI 模型健康度定时推送"


def interval_minutes_to_cron(interval_minutes: int) -> str:
    if interval_minutes < 60 and 60 % interval_minutes == 0:
        return f"*/{interval_minutes} * * * *"
    if interval_minutes % 60 == 0:
        interval_hours = interval_minutes // 60
        if interval_hours < 24 and 24 % interval_hours == 0:
            return f"0 */{interval_hours} * * *"
        if interval_hours == 24:
            return "0 0 * * *"
    raise PluginConfigurationError(
        "push_interval_minutes 仅支持 15/30/60/120/180/360/720/1440。"
    )


class PushJobScheduler:
    """负责注册/清理 AstrBot cron 定时任务。"""

    def __init__(
        self,
        context: Context,
        star: Star,
        settings_provider: Callable[[], PluginSettings],
        report_service_factory: Callable[[PluginSettings], NewApiHealthReportService],
    ) -> None:
        self.context = context
        self.star = star
        self.settings_provider = settings_provider
        self.report_service_factory = report_service_factory
        self._job_id: str | None = None
        self._run_lock = asyncio.Lock()

    async def initialize(self) -> None:
        cron_manager = getattr(self.context, "cron_manager", None)
        if cron_manager is None:
            logger.warning("当前 AstrBot 未提供 cron_manager，跳过 NewAPI 定时推送初始化。")
            return

        await self._cleanup_stale_jobs()

        settings = self.settings_provider()
        if not settings.push_enabled:
            logger.info("NewAPI 模型健康度定时推送未启用。")
            return
        try:
            settings.require_base_url()
        except PluginConfigurationError as exc:
            logger.warning(f"NewAPI 定时推送未注册：{exc}")
            return
        if not settings.enabled_targets:
            logger.warning("NewAPI 定时推送已启用，但未配置任何启用状态的 push_targets。")
            return

        cron_expression = interval_minutes_to_cron(settings.push_interval_minutes)
        job = await cron_manager.add_basic_job(
            name=PLUGIN_JOB_NAME,
            cron_expression=cron_expression,
            handler=self.run_push_job,
            description="按插件配置向固定会话推送 NewAPI 模型健康度图卡。",
            payload={"plugin_job_key": PLUGIN_JOB_KEY},
            enabled=True,
            persistent=False,
        )
        self._job_id = job.job_id
        logger.info(
            f"NewAPI 模型健康度定时推送已注册：interval={settings.push_interval_minutes} 分钟, "
            f"targets={len(settings.enabled_targets)}"
        )

    async def terminate(self) -> None:
        cron_manager = getattr(self.context, "cron_manager", None)
        if cron_manager is None:
            return
        if self._job_id:
            await cron_manager.delete_job(self._job_id)
            self._job_id = None

    async def run_push_job(self, **_: Any) -> None:
        if self._run_lock.locked():
            logger.warning("NewAPI 模型健康度定时推送上一次任务尚未完成，本次跳过。")
            return

        async with self._run_lock:
            settings = self.settings_provider()
            if not settings.push_enabled:
                logger.info("定时推送任务触发时检测到 push_enabled=false，跳过。")
                return
            if not settings.enabled_targets:
                logger.warning("定时推送任务触发，但没有可用 push_targets。")
                return

            service = self.report_service_factory(settings)
            try:
                report = await service.build_report(self.star)
            except RemoteSelectionEmptyError as exc:
                logger.warning(f"定时推送跳过：{exc}")
                return
            except (PluginConfigurationError, NewApiRequestError) as exc:
                logger.error(f"定时推送失败：{exc}")
                return
            except Exception as exc:  # noqa: BLE001
                logger.exception(f"定时推送出现未预期错误：{exc}")
                return

            summary = (
                f"NewAPI 模型健康度 | "
                f"{report.snapshot.remote_config.time_window} | "
                f"{report.snapshot.fetched_at.strftime('%Y-%m-%d %H:%M:%S %Z')}"
            )
            for target in settings.enabled_targets:
                await self._send_report_to_target(
                    target_group_id=target.group_id,
                    summary=summary,
                    report=report,
                )

    async def _send_report_to_target(
        self,
        target_group_id: str,
        summary: str,
        report,
    ) -> None:
        session = MessageSesion("aiocqhttp", MessageType.GROUP_MESSAGE, target_group_id)
        for index, page in enumerate(report.pages):
            chain = MessageChain()
            if index == 0:
                chain.message(summary)
            chain.url_image(page.image_url)
            try:
                sent = await self.context.send_message(session, chain)
            except Exception as exc:  # noqa: BLE001
                logger.error(f"向群 {target_group_id} 推送健康度图失败：{exc}")
                return
            if not sent:
                logger.warning(f"向群 {target_group_id} 推送健康度图失败：平台未找到或未发送。")
                return

    async def _cleanup_stale_jobs(self) -> None:
        cron_manager = getattr(self.context, "cron_manager", None)
        if cron_manager is None:
            return

        try:
            jobs = await cron_manager.list_jobs("basic")
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"读取 AstrBot cron jobs 失败，无法清理旧任务：{exc}")
            return

        for job in jobs:
            payload = getattr(job, "payload", None)
            if isinstance(payload, dict) and payload.get("plugin_job_key") == PLUGIN_JOB_KEY:
                await cron_manager.delete_job(job.job_id)
