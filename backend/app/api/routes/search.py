from fastapi import APIRouter, HTTPException, status

from app.rag.embedding_service import EmbeddingError
from app.rag.retriever import Retriever
from app.schemas.search import SearchRequest, SearchResponse, SearchResultItem

router = APIRouter(prefix="/search", tags=["search"])

retriever = Retriever()


@router.post("", response_model=SearchResponse)
def search(payload: SearchRequest) -> SearchResponse:
    """Busqueda semantica: embebe la consulta y devuelve los chunks mas relevantes."""
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
    return SearchResponse(query=payload.query, total=len(results), results=results)
