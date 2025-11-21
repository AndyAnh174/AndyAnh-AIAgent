import logging
from typing import Any, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import Settings

logger = logging.getLogger(__name__)


class ReminderScheduler:
    _scheduler: AsyncIOScheduler | None = None

    @classmethod
    async def initialize(cls, settings: Settings) -> None:
        if cls._scheduler:
            return
        cls._scheduler = AsyncIOScheduler(timezone="UTC")
        cls._scheduler.add_jobstore("memory")
        cls._scheduler.start()
        logger.info("Reminder scheduler started")

    @classmethod
    async def shutdown(cls) -> None:
        if cls._scheduler:
            cls._scheduler.shutdown(wait=False)
        cls._scheduler = None

    @classmethod
    def add_job(cls, func: Callable[..., Any], trigger: str, **kwargs: Any) -> None:
        if cls._scheduler is None:
            raise RuntimeError("Scheduler not initialized")
        cls._scheduler.add_job(func, trigger, **kwargs)

