from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.data.seed_incidents import get_seed_incidents
from app.hindsight.client import get_hindsight_manager
from app.repositories.incident_repository import get_incident_repository

logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan managing startup probes and clean resource shutdown."""
    settings = get_settings()
    setup_logging(settings.log_level)

    logger.info("Starting %s in [%s] mode", settings.app_name, settings.app_env)
    logger.info("Configured Hindsight Base URL: %s", settings.hindsight_base_url)
    logger.info("Configured Hindsight Memory Bank: %s", settings.hindsight_bank_id)

    # Populate in-memory repository with initial seed data if empty
    repo = get_incident_repository()
    if repo.count() == 0:
        seed_count = repo.seed(get_seed_incidents())
        logger.info("Seeded %d historical incidents into in-memory repository", seed_count)

    # Perform non-blocking connectivity probe during startup
    manager = get_hindsight_manager()
    status = await manager.check_connection()
    if status.connected:
        logger.info(
            "Hindsight connection verified (server version: %s)",
            status.server_version,
        )
    else:
        logger.warning(
            "Hindsight memory server is currently offline or unreachable: %s. "
            "App will run, but memory operations will fail until Hindsight is started.",
            status.error,
        )

    yield

    # Clean up client sessions on shutdown
    logger.info("Shutting down %s...", settings.app_name)
    await manager.close()
    logger.info("Shutdown completed cleanly.")


def create_application() -> FastAPI:
    """Factory function to build and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="Production-oriented AI Incident Response Agent with Hindsight long-term memory.",
        version="0.2.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Configure Cross-Origin Resource Sharing (CORS)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API Routes
    app.include_router(api_router)

    @app.get("/", tags=["Root"])
    async def root_info() -> dict:
        """Root metadata endpoint providing links to documentation and status."""
        return {
            "name": settings.app_name,
            "version": "0.2.0",
            "environment": settings.app_env,
            "endpoints": {
                "health": "/health",
                "docs": "/docs",
                "incidents": "/api/v1/incidents",
                "hindsight_status": "/api/v1/hindsight/status",
            },
        }

    return app


app = create_application()
