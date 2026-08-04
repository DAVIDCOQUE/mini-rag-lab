import logging
import uuid
from collections.abc import Sequence

from fastapi import APIRouter, Depends, HTTPException, status
from qdrant_client.models import ScoredPoint
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.rag.embedding_service import EmbeddingError
from app.rag.llm_service import LLMError
from app.schemas.chat import ChatRequest, ChatResponse, ChatSource
from app.services import rag_service
from app.services.document_service import DocumentNotFoundError, get_document

logger = logging.getLogger("mini_rag_lab")

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    """RAG conversacional. El router decide si la pregunta necesita el corpus o no."""
    logger.info("Pregunta recibida: %s", request.message)

    try:
        outcome = rag_service.answer_question(db, request.message)
    except EmbeddingError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No fue posible generar el embedding de la consulta (¿Ollama activo?).",
        )
    except LLMError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No fue posible conectar con Ollama.",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No fue posible realizar la búsqueda (¿Qdrant activo?).",
        )

    # Solo el camino institucional tiene fuentes que citar.
    sources = [
        ChatSource(filename=filename, score=point.score, chunk=point.payload["content"])
        for point, filename in zip(outcome.points, _resolve_filenames(db, outcome.points))
    ]

    return ChatResponse(question=request.message, answer=outcome.answer, sources=sources)


def _resolve_filenames(db: Session, points: Sequence[ScoredPoint]) -> list[str]:
    """Nombre original de cada chunk recuperado, cacheado por documento para no repetir consultas."""
    cache: dict[str, str] = {}
    filenames = []
    for point in points:
        document_id = point.payload["document_id"]
        if document_id not in cache:
            try:
                cache[document_id] = get_document(db, uuid.UUID(document_id)).original_name
            except DocumentNotFoundError:
                cache[document_id] = "Documento eliminado"
        filenames.append(cache[document_id])
    return filenames
