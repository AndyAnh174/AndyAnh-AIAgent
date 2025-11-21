from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.routes import health, journal, retrieval, reminders, search, admin, media, analysis
from app.core.config import Settings, get_settings
from app.core.events import create_start_app_handler, create_stop_app_handler
from app.core.logging import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create configured FastAPI application."""
    configure_logging()

    app = FastAPI(
        title="AI Life Companion",
        description=(
            "Self-hosted AI journal & digital twin backend with GraphRAG, proactive agent, "
            "and strong security guarantees."
        ),
        version="1.0.0",
    )

    _settings = settings or get_settings()
    app.state.settings = _settings

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_settings.normalized_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(journal.router, prefix="/journal", tags=["journal"])
    app.include_router(retrieval.router, prefix="/retrieval", tags=["retrieval"])
    app.include_router(reminders.router, prefix="/reminders", tags=["reminders"])
    app.include_router(search.router, tags=["search"])
    app.include_router(admin.router, tags=["admin"])
    app.include_router(media.router, prefix="/api", tags=["media"])
    app.include_router(analysis.router)

    Instrumentator().instrument(app).expose(app)
    app.add_event_handler("startup", create_start_app_handler(app))
    app.add_event_handler("shutdown", create_stop_app_handler(app))

    return app


app = create_app()

