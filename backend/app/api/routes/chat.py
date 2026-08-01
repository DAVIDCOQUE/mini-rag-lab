import logging
import time
import uuid
from collections.abc import Sequence

from fastapi import APIRouter, Depends, HTTPException, status
from qdrant_client.models import ScoredPoint
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.rag.embedding_service import EmbeddingError
from app.rag.llm_service import LLMError, generate
from app.rag.prompt_builder import NO_ANSWER_MESSAGE, build_prompt
from app.rag.retriever import Retriever
from app.schemas.chat import ChatRequest, ChatResponse, ChatSource
from app.services.document_service import DocumentNotFoundError, get_document

logger = logging.getLogger("mini_rag_lab")

router = APIRouter(tags=["chat"])
retriever = Retriever()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    """RAG conversacional: recupera contexto relevante y genera una respuesta con el LLM."""
    logger.info("Pregunta recibida: %s", request.message)

    try:
        points = retriever.search(request.message, settings.CHAT_TOP_K)
    except EmbeddingError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No fue posible generar el embedding de la consulta (¿Ollama activo?).",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No fue posible realizar la búsqueda (¿Qdrant activo?).",
        )

    # Corte previo al LLM: si no hay suficientes chunks o el mejor no es lo bastante
    # relevante, no tiene sentido gastar una llamada al modelo (y se evita que
    # alucine sobre contexto irrelevante). Ver comentario de CHAT_MIN_SCORE en config.
    if len(points) < settings.CHAT_MIN_RESULTS or points[0].score < settings.CHAT_MIN_SCORE:
        logger.info(
            "Contexto insuficiente para '%s' (chunks=%d, top_score=%s); no se llama al LLM.",
            request.message,
            len(points),
            points[0].score if points else None,
        )
        return ChatResponse(question=request.message, answer=NO_ANSWER_MESSAGE, sources=[])

    chunks = [point.payload["content"] for point in points]
    prompt = build_prompt(request.message, chunks)

    start = time.perf_counter()
    try:
        answer = generate(prompt)
    except LLMError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No fue posible conectar con Ollama.",
        )
    elapsed = time.perf_counter() - start
    logger.info("Respuesta del modelo '%s' en %.2fs", settings.LLM_MODEL, elapsed)

    sources = [
        ChatSource(filename=filename, score=point.score, chunk=point.payload["content"])
        for point, filename in zip(points, _resolve_filenames(db, points))
    ]

    return ChatResponse(question=request.message, answer=answer, sources=sources)


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
