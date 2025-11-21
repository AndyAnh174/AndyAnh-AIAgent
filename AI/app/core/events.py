import logging
from typing import Callable

from fastapi import FastAPI

from app.db.session import close_db_connection, connect_to_db
from app.services.graph import GraphRAGService
from app.services.scheduler import ReminderScheduler
from app.services.session_manager import SessionManager
from app.services.storage import StorageService

logger = logging.getLogger(__name__)


def create_start_app_handler(app: FastAPI) -> Callable[[], None]:
    async def start_app() -> None:
        logger.info("Starting AI Life Companion backend")
        settings = app.state.settings
        logger.info("API Keys configured: %s", list(settings.normalized_api_keys))
        await connect_to_db(settings.database_url)
        await ReminderScheduler.initialize(settings)
        await SessionManager.initialize(settings)
        StorageService.configure(settings)
        try:
            GraphRAGService.configure(settings)
        except Exception as exc:
            logger.warning("GraphRAG initialization failed (will retry on first use): %s", exc)

    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable[[], None]:
    async def stop_app() -> None:
        logger.info("Shutting down AI Life Companion backend")
        await close_db_connection()
        await ReminderScheduler.shutdown()
        await SessionManager.shutdown()

    return stop_app

