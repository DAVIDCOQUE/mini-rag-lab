from fastapi import APIRouter

from app.core.config import settings
from app.schemas.health import HealthResponse
from app.services.health_service import check_database, check_ollama, check_qdrant

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Estado del servicio verificando la conectividad real de PostgreSQL, Qdrant y Ollama."""
    return HealthResponse(
        status="ok",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        database=check_database(),
        qdrant=check_qdrant(),
        ollama=check_ollama(),
    )
