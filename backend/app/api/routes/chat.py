import logging
import uuid
from collections.abc import Sequence

from fastapi import APIRouter, Depends, HTTPException, status
from qdrant_client.models import ScoredPoint
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.rag.embedding_service import EmbeddingError
from app.rag.llm_service import LLMError
from app.models.document import Document
from app.schemas.chat import ChatDownload, ChatRequest, ChatResponse, ChatSource
from app.services import download_service, rag_service
from app.services.document_service import DocumentNotFoundError, get_document

logger = logging.getLogger("mini_rag_lab")

router = APIRouter(tags=["chat"])



@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    """RAG conversacional. El router decide si la pregunta necesita el corpus o no."""
    logger.info("Pregunta recibida: %s", request.message)

    try:
        outcome = rag_service.answer_question(db, request.message, history=request.history)
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
    documents = _resolve_documents(db, outcome.points)
    sources = [
        ChatSource(
            filename=documents[point.payload["document_id"]].original_name
            if documents[point.payload["document_id"]]
            else "Documento eliminado",
            score=point.score,
            chunk=point.payload["content"],
        )
        for point in outcome.points
    ]

    # outcome.forms son solo los formatos entregados: los ofrecidos van en el texto.
    return ChatResponse(
        question=request.message, answer=outcome.answer, sources=sources, downloads=_downloads(outcome.forms)
    )


def _resolve_documents(db: Session, points: Sequence[ScoredPoint]) -> dict[str, Document | None]:
    """Documento de cada chunk recuperado, una consulta por documento; None si se borro."""
    documents: dict[str, Document | None] = {}
    for point in points:
        document_id = point.payload["document_id"]
        if document_id not in documents:
            try:
                documents[document_id] = get_document(db, uuid.UUID(document_id))
            except DocumentNotFoundError:
                documents[document_id] = None
    return documents


def _downloads(forms: Sequence[tuple[Document, float]]) -> list[ChatDownload]:
    """Enlace temporal de cada formato elegido para la pregunta."""
    downloads = []
    for form, _ in forms:
        link = download_service.create_link(form.id)
        downloads.append(
            ChatDownload(
                document_id=form.id,
                filename=form.original_name,
                url=link.url,
                qr_url=link.qr_url,
                expires_at=link.expires_at,
            )
        )
    return downloads
