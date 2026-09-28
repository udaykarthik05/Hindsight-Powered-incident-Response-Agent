from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.config import Settings, get_settings

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Standard application health check response."""
    status: str
    app: str
    environment: str
    timestamp: str


@router.get("/health", response_model=HealthResponse)
async def get_health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """
    Application health endpoint.
    
    Returns 200 OK indicating the FastAPI application is alive and responding.
    """
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        environment=settings.app_env,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
