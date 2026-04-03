"""FastAPI application entry point.

Creates the ASGI app, mounts routers, and starts uvicorn when run directly.
"""

from __future__ import annotations

import logging
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import load_settings
from backend.routers.openai_compat import create_openai_router
from backend.services.gemini_client import GeminiCliClient, GeminiCliConfig

logging.basicConfig(
    level=logging.INFO,
    format="[%(name)s] %(levelname)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("safegemini2api")


def create_app() -> FastAPI:
    """Build the FastAPI application with all dependencies wired up."""
    settings = load_settings()

    app = FastAPI(
        title="safegemini2api",
        description="OpenAI-compatible adapter backed by Gemini CLI",
        version="0.2.0",
    )

    # CORS – allow the Vue dev-server and any local origin
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Gemini CLI client (immutable config)
    cli_config = GeminiCliConfig(
        command=settings.gemini_cli_command,
        extra_args=settings.get_extra_args(),
        workdir=settings.get_workdir(),
        timeout_ms=settings.request_timeout_ms,
    )
    gemini_client = GeminiCliClient(cli_config)

    # Mount routes
    openai_router = create_openai_router(settings, gemini_client)
    app.include_router(openai_router)

    # Health check
    @app.get("/healthz")
    async def healthz():
        return {"ok": True}

    # Root redirect
    @app.get("/")
    async def root():
        return {"message": "safegemini2api is running. API at /v1/"}

    logger.info(
        "App created — host=%s port=%s auth=%s model=%s",
        settings.host,
        settings.port,
        "enabled" if settings.openai_api_key else "disabled",
        settings.default_model,
    )

    return app


app = create_app()


if __name__ == "__main__":
    settings = load_settings()
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
