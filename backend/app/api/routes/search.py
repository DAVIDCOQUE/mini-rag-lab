import logging
import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.rag.embedding_service import EmbeddingError
from app.rag.llm_service import LLMError, generate
from app.rag.prompt_builder import NO_ANSWER_MESSAGE, build_prompt
from app.rag.retriever import Retriever
from app.schemas.search import (
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    SearchTimings,
)
from app.services import prompt_service
from app.services.prompt_service import PromptNotFoundError

logger = logging.getLogger("mini_rag_lab")

router = APIRouter(prefix="/search", tags=["search"])

retriever = Retriever()


@router.post("", response_model=SearchResponse)
def search(payload: SearchRequest, db: Session = Depends(get_db)) -> SearchResponse:
    """Busqueda semantica: embebe la consulta y devuelve los chunks mas relevantes.

    Con generate=True esos mismos chunks se pasan al LLM como contexto, de modo que
    una sola respuesta expone el flujo RAG completo y el coste de cada etapa.
    """
    started = time.perf_counter()

    try:
        points = retriever.search(payload.query, payload.limit)
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

    retrieval_ms = (time.perf_counter() - started) * 1000

    results = [
        SearchResultItem(
            document_id=point.payload["document_id"],
            page=point.payload["page"],
            chunk_index=point.payload["chunk_index"],
            content=point.payload["content"],
            score=point.score,
        )
        for point in points
    ]

    answer: str | None = None
    generation_ms: float | None = None
    generation_skipped = False
    prompt_code: str | None = None

    if payload.generate:
        try:
            system_prompt, prompt_code = prompt_service.resolve_prompt(db, payload.prompt_code)
        except PromptNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No existe el prompt '{payload.prompt_code}'.",
            )

        # Mismo corte de calidad que /chat: sin contexto suficiente no se gasta una
        # llamada al modelo ni se le da pie a inventar sobre chunks irrelevantes.
        if len(points) < settings.CHAT_MIN_RESULTS or points[0].score < settings.CHAT_MIN_SCORE:
            logger.info(
                "Contexto insuficiente para '%s' (chunks=%d, top_score=%s); no se llama al LLM.",
                payload.query,
                len(points),
                points[0].score if points else None,
            )
            answer = NO_ANSWER_MESSAGE
            generation_skipped = True
        else:
            chunks = [point.payload["content"] for point in points]
            prompt = build_prompt(payload.query, chunks, system_prompt)

            generation_started = time.perf_counter()
            try:
                answer = generate(prompt)
            except LLMError:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="No fue posible conectar con Ollama.",
                )
            generation_ms = (time.perf_counter() - generation_started) * 1000
            logger.info(
                "Respuesta del modelo '%s' en %.2fs", settings.LLM_MODEL, generation_ms / 1000
            )

    return SearchResponse(
        query=payload.query,
        total=len(results),
        results=results,
        answer=answer,
        generation_skipped=generation_skipped,
        prompt_code=prompt_code,
        timings=SearchTimings(
            retrieval_ms=round(retrieval_ms, 1),
            generation_ms=round(generation_ms, 1) if generation_ms is not None else None,
            total_ms=round((time.perf_counter() - started) * 1000, 1),
        ),
    )
