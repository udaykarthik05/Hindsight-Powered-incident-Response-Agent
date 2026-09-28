from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.hindsight import router as hindsight_router
from app.api.routes.incidents import router as incidents_router

# Root API router
api_router = APIRouter()

# Register routes
api_router.include_router(health_router)
api_router.include_router(hindsight_router, prefix="/api/v1")
api_router.include_router(incidents_router, prefix="/api/v1")
