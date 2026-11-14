import logging
import re
import uuid
from collections.abc import Sequence
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.repositories import document_repository as repository
from app.schemas.document import DocumentKind, DocumentUpdate

logger = logging.getLogger("mini_rag_lab")

ALLOWED_EXTENSION = "pdf"
ALLOWED_MIME = "application/pdf"
PDF_MAGIC = b"%PDF"


class DocumentNotFoundError(Exception):
    """El documento solicitado no existe."""


class InvalidDocumentError(Exception):
    """El archivo no cumple las reglas de subida (tipo o tamano)."""


class VectorCleanupError(Exception):
    """No se pudieron borrar los vectores de un documento que pasa a ser formato."""


def _originals_dir() -> Path:
    """Ruta storage/documents/originals, creada si no existe."""
    path = Path(settings.STORAGE_DIR) / "documents" / "originals"
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_document(
    db: Session,
    file: UploadFile,
    kind: DocumentKind = DocumentKind.KNOWLEDGE,
    description: str | None = None,
    form_code: str | None = None,
    public_url: str | None = None,
) -> Document:
    """Valida el PDF, lo guarda en disco con nombre UUID y registra el documento."""
    description = _clean_description(kind, description)
    public_url = _clean_public_url(public_url) if kind is DocumentKind.FORM else None
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
        kind=kind.value,
        description=description,
        # Sin codigo indicado se intenta leer del propio PDF.
        form_code=_clean_code(form_code) or (_extract_code(destination) if kind is DocumentKind.FORM else None),
        public_url=public_url,
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
    previous_kind = document.kind
    for field, value in data.items():
        setattr(document, field, value.value if hasattr(value, "value") else value)
    document.description = _clean_description(DocumentKind(document.kind), document.description)
    document.form_code = _clean_code(document.form_code) if document.kind == DocumentKind.FORM.value else None
    is_form = document.kind == DocumentKind.FORM.value
    document.public_url = _clean_public_url(document.public_url) if is_form else None
    if not is_form:
        document.cloud_item_id = None

    if document.kind != previous_kind:
        # Un documento que pasa a formato no puede seguir en la busqueda. Aqui el borrado
        # no es best-effort: si Qdrant falla, el cambio no se guarda.
        if document.kind == DocumentKind.FORM.value:
            try:
                from app.rag.qdrant_service import QdrantService

                QdrantService().delete_by_document(document.id)
            except Exception as exc:
                db.rollback()
                raise VectorCleanupError("No se pudieron retirar sus fragmentos de Qdrant.") from exc
        # En ambos sentidos queda sin indexar: un formato nunca se indexa, y uno de
        # informacion que venia de formato aun no tiene fragmentos.
        document.status = "PENDING"
    return repository.update(db, document)


# "CODIGO: R-GA004" en la cabecera de los formatos institucionales.
_CODE_IN_PDF = re.compile(r"C[OÓ]DIGO\s*:?\s*([A-Z]{1,6}(?:-[A-Z]{1,6})?-?\s?\d{2,5})")


def _extract_code(path: Path) -> str | None:
    """Codigo impreso en el formato, o None si no trae (no todos lo tienen)."""
    try:
        import fitz

        with fitz.open(path) as pdf:
            text = " ".join(" ".join(page.get_text() for page in pdf).split()).upper()
    except Exception as exc:
        logger.warning("No se pudo leer el codigo del formato %s: %s", path, exc)
        return None
    match = _CODE_IN_PDF.search(text)
    return _clean_code(match.group(1)) if match else None


def upload_form_to_cloud(db: Session, document_id: uuid.UUID) -> Document:
    """Sube el formato a OneDrive y guarda su enlace publico; si ya estaba, lo reemplaza."""
    from app.services import onedrive_service

    document = get_document(db, document_id)
    if document.kind != DocumentKind.FORM.value:
        raise InvalidDocumentError("Solo los formatos se suben a OneDrive.")
    path = Path(document.storage_path)
    if not path.is_file():
        raise InvalidDocumentError("El archivo del formato no está en el servidor.")

    cloud_file = onedrive_service.upload_form(document.original_name, path.read_bytes(), document.cloud_item_id)
    document.cloud_item_id = cloud_file.item_id
    document.public_url = cloud_file.public_url
    return repository.update(db, document)


def _clean_public_url(url: str | None) -> str | None:
    text = (url or "").strip()
    if not text:
        return None
    # El enlace termina dentro de un QR que abre un celular: solo http(s).
    if not text.lower().startswith(("https://", "http://")):
        raise InvalidDocumentError("El enlace público debe empezar por https://")
    if len(text) > 1024:
        raise InvalidDocumentError("El enlace público es demasiado largo.")
    return text


def _clean_code(code: str | None) -> str | None:
    text = " ".join((code or "").split()).upper()
    return text or None


def _clean_description(kind: DocumentKind, description: str | None) -> str | None:
    """Los formatos exigen descripcion: es lo unico con lo que se decide ofrecerlos."""
    text = (description or "").strip() or None
    if kind is DocumentKind.FORM and not text:
        raise InvalidDocumentError("Un formato necesita una descripción de para qué sirve.")
    return text


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
