import logging
import urllib.request

from sqlalchemy import text

from app.core.config import settings
from app.database.session import engine

logger = logging.getLogger("mini_rag_lab")

CONNECTED = "connected"
DISCONNECTED = "disconnected"

# Timeout corto para no bloquear /health cuando un servicio esta caido.
TIMEOUT_SECONDS = 2.0


def check_database() -> str:
    """Comprueba PostgreSQL abriendo una conexion y ejecutando SELECT 1."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return CONNECTED
    except Exception as exc:
        logger.warning("PostgreSQL no disponible: %s", exc)
        return DISCONNECTED


def check_qdrant() -> str:
    """Comprueba Qdrant consultando la lista de colecciones (solo conectividad)."""
    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            timeout=TIMEOUT_SECONDS,
        )
        try:
            client.get_collections()
            return CONNECTED
        finally:
            client.close()
    except Exception as exc:
        logger.warning("Qdrant no disponible: %s", exc)
        return DISCONNECTED


def check_ollama() -> str:
    """Comprueba Ollama con una peticion GET a /api/tags."""
    url = f"{settings.OLLAMA_URL.rstrip('/')}/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as resp:
            if resp.status == 200:
                return CONNECTED
            logger.warning("Ollama respondio con estado %s", resp.status)
            return DISCONNECTED
    except Exception as exc:
        logger.warning("Ollama no disponible: %s", exc)
        return DISCONNECTED
