"""Entry point for running the API service."""

import uvicorn

from libs.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "services.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
