import logging
import uuid
from collections.abc import Sequence
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.repositories import document_repository as repository
from app.schemas.document import DocumentUpdate

logger = logging.getLogger("mini_rag_lab")

ALLOWED_EXTENSION = "pdf"
ALLOWED_MIME = "application/pdf"
PDF_MAGIC = b"%PDF"


class DocumentNotFoundError(Exception):
    """El documento solicitado no existe."""


class InvalidDocumentError(Exception):
    """El archivo no cumple las reglas de subida (tipo o tamano)."""


def _originals_dir() -> Path:
    """Ruta storage/documents/originals, creada si no existe."""
    path = Path(settings.STORAGE_DIR) / "documents" / "originals"
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_document(db: Session, file: UploadFile) -> Document:
    """Valida el PDF, lo guarda en disco con nombre UUID y registra el documento."""
    filename = file.filename or ""
    extension = Path(filename).suffix.lower().lstrip(".")
    if extension != ALLOWED_EXTENSION:
        raise InvalidDocumentError("Solo se permiten archivos PDF.")

    # Leer como maximo el limite + 1 byte para detectar excesos sin cargar archivos enormes.
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    content = file.file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise InvalidDocumentError(f"El archivo supera el tamano maximo de {settings.MAX_UPLOAD_MB} MB.")
    if not content.startswith(PDF_MAGIC):
        raise InvalidDocumentError("El archivo no es un PDF valido.")

    stored_name = f"{uuid.uuid4()}.{ALLOWED_EXTENSION}"
    destination = _originals_dir() / stored_name
    destination.write_bytes(content)

    document = Document(
        original_name=filename,
        stored_name=stored_name,
        storage_path=destination.as_posix(),
        mime_type=file.content_type or ALLOWED_MIME,
        extension=ALLOWED_EXTENSION,
        size_bytes=len(content),
        status="PENDING",
    )
    document = repository.create(db, document)
    logger.info("Documento creado: %s (%s)", document.original_name, document.id)
    return document


def list_documents(db: Session) -> Sequence[Document]:
    return repository.list_all(db)


def get_document(db: Session, document_id: uuid.UUID) -> Document:
    document = repository.get(db, document_id)
    if document is None:
        raise DocumentNotFoundError
    return document


def update_document(db: Session, document_id: uuid.UUID, payload: DocumentUpdate) -> Document:
    document = get_document(db, document_id)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(document, field, value.value if hasattr(value, "value") else value)
    return repository.update(db, document)


def delete_document(db: Session, document_id: uuid.UUID) -> None:
    """Elimina el archivo fisico, sus vectores en Qdrant y por ultimo el registro."""
    document = get_document(db, document_id)
    file_path = Path(document.storage_path)
    try:
        file_path.unlink(missing_ok=True)
    except OSError as exc:
        logger.warning("No se pudo eliminar el archivo %s: %s", file_path, exc)

    # Borrar vectores en Qdrant (best-effort: no bloquea el borrado si Qdrant esta caido).
    try:
        from app.rag.qdrant_service import QdrantService

        QdrantService().delete_by_document(document.id)
    except Exception as exc:
        logger.warning("No se pudieron eliminar los vectores en Qdrant: %s", exc)

    repository.delete(db, document)
    logger.info("Documento eliminado: %s", document_id)
