import logging
import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.rag.embedding_service import EmbeddingError
from app.rag.llm_service import LLMError
from app.schemas.search import (
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    SearchTimings,
)
from app.services import rag_service
from app.services.prompt_service import PromptNotFoundError

logger = logging.getLogger("mini_rag_lab")

router = APIRouter(prefix="/search", tags=["search"])

# Se reutiliza el retriever del servicio en lugar de crear otro: cada Retriever trae
# su propio reranker, y cargar dos veces el mismo cross-encoder solo duplica memoria.
retriever = rag_service.retriever

UNREACHABLE_EMBEDDING = "No fue posible generar el embedding de la consulta (¿Ollama activo?)."
UNREACHABLE_SEARCH = "No fue posible realizar la búsqueda (¿Qdrant activo?)."


@router.post("", response_model=SearchResponse)
def search(payload: SearchRequest, db: Session = Depends(get_db)) -> SearchResponse:
    """Busqueda semantica y, opcionalmente, el flujo RAG completo.

    Sin generate solo recupera: es la busqueda pura, util para medir recuperacion sin
    coste de modelo. Con generate se enruta la consulta y solo el camino institucional
    llega a Qdrant, de modo que la vista ensena que decidio el sistema y que costo.
    """
    started = time.perf_counter()

    if not payload.generate:
        try:
            points = retriever.search(payload.query, payload.limit)
        except EmbeddingError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=UNREACHABLE_EMBEDDING
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=UNREACHABLE_SEARCH
            )

        retrieval_ms = (time.perf_counter() - started) * 1000
        return SearchResponse(
            query=payload.query,
            total=len(points),
            results=_to_items(points),
            timings=SearchTimings(
                retrieval_ms=round(retrieval_ms, 1),
                total_ms=round(retrieval_ms, 1),
            ),
        )

    try:
        outcome = rag_service.answer_question(db, payload.query, payload.limit, payload.prompt_code)
    except PromptNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe el prompt '{payload.prompt_code}'.",
        )
    except EmbeddingError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=UNREACHABLE_EMBEDDING
        )
    except LLMError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="No fue posible conectar con Ollama."
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=UNREACHABLE_SEARCH
        )

    results = _to_items(outcome.points)
    return SearchResponse(
        query=payload.query,
        total=len(results),
        results=results,
        answer=outcome.answer,
        generation_skipped=outcome.generation_skipped,
        prompt_code=outcome.prompt_code,
        route=outcome.route.value,
        route_scores=outcome.route_scores,
        timings=SearchTimings(
            routing_ms=outcome.routing_ms,
            retrieval_ms=outcome.retrieval_ms,
            generation_ms=outcome.generation_ms,
            total_ms=round((time.perf_counter() - started) * 1000, 1),
        ),
    )


def _to_items(points) -> list[SearchResultItem]:
    return [
        SearchResultItem(
            document_id=point.payload["document_id"],
            page=point.payload["page"],
            chunk_index=point.payload["chunk_index"],
            content=point.payload["content"],
            score=point.score,
        )
        for point in points
    ]
