"""FastAPI application factory."""

from fastapi import FastAPI

from libs.config import get_settings
from services.api.routes import assets, events, health, indicators

settings = get_settings()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )

    # Include routers
    application.include_router(health.router, tags=["health"])
    application.include_router(assets.router, prefix=settings.api_prefix, tags=["assets"])
    application.include_router(indicators.router, prefix=settings.api_prefix, tags=["indicators"])
    application.include_router(events.router, prefix=settings.api_prefix, tags=["events"])

    return application


app = create_app()
