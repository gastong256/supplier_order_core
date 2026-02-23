from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DBSession
from app.core.config import settings
from app.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, include_in_schema=True)
async def health_check(db: DBSession) -> HealthResponse:
    """Liveness + readiness check (includes DB connectivity)."""
    try:
        await db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "unavailable"

    return HealthResponse(
        status="ok" if db_status == "ok" else "degraded",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        database=db_status,
    )
