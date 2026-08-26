from datetime import datetime, timezone
from fastapi import APIRouter, status
from pydantic import BaseModel
from app.config import settings

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    environment: str
    timestamp: str


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    response_model=HealthResponse,
    summary="API Health Check",
    description="Returns current system health status, application name, version, and server timestamp.",
)
def get_health() -> HealthResponse:
    """Health check endpoint returning application status."""
    return HealthResponse(
        status="ok",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
