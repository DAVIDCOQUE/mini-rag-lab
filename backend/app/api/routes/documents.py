import io
import uuid
from pathlib import Path

import segno

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from app.core.security import require_maintainer
from app.database.session import get_db
from app.schemas.document import CloudStatus, DocumentKind, DocumentResponse, DocumentUpdate
from app.schemas.processing import IndexedChunks, IndexResult, ProcessingResult
from app.services import document_service as service
from app.services import download_service, onedrive_service
from app.services.download_service import InvalidDownloadTokenError
from app.services.onedrive_service import CloudStorageError
from app.services.document_processing_service import (
    DocumentProcessingService,
    EmptyDocumentError,
    FileMissingError,
    FormNotIndexableError,
    IndexingError,
)
from app.services.document_service import (
    DocumentNotFoundError,
    InvalidDocumentError,
    VectorCleanupError,
)

router = APIRouter(prefix="/documents", tags=["documents"])

processing_service = DocumentProcessingService()


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_maintainer)],
)
def create_document(
    file: UploadFile = File(...),
    kind: DocumentKind = Form(DocumentKind.KNOWLEDGE),
    description: str | None = Form(None),
    form_code: str | None = Form(None),
    public_url: str | None = Form(None),
    db: Session = Depends(get_db),
) -> DocumentResponse:
    try:
        return service.create_document(db, file, kind, description, form_code, public_url)
    except InvalidDocumentError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("", response_model=list[DocumentResponse], dependencies=[Depends(require_maintainer)])
def list_documents(db: Session = Depends(get_db)) -> list[DocumentResponse]:
    return service.list_documents(db)


@router.get("/cloud-status", response_model=CloudStatus, dependencies=[Depends(require_maintainer)])
def cloud_status() -> CloudStatus:
    return CloudStatus(enabled=onedrive_service.is_enabled())


@router.post(
    "/{document_id}/cloud-upload",
    response_model=DocumentResponse,
    dependencies=[Depends(require_maintainer)],
)
def upload_to_cloud(document_id: uuid.UUID, db: Session = Depends(get_db)) -> DocumentResponse:
    """Sube el formato a OneDrive con enlace publico; si ya estaba subido, lo reemplaza."""
    try:
        return service.upload_form_to_cloud(db, document_id)
    except DocumentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado.")
    except InvalidDocumentError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except CloudStorageError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))



# Declarada antes de /{document_id}: si no, "download" se intentaria leer como un id.
@router.get("/download", response_class=FileResponse)
def download_document(token: str, db: Session = Depends(get_db)) -> FileResponse:
    """Descarga publica de un formato a traves del enlace firmado que lleva el QR."""
    unavailable = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="El enlace no es válido o ya caducó."
    )
    try:
        document = service.get_document(db, download_service.read_token(token))
    except (InvalidDownloadTokenError, DocumentNotFoundError):
        raise unavailable
    # Se comprueba al descargar, no solo al emitir: si el documento deja de ser formato,
    # los enlaces que ya estuvieran circulando dejan de servir.
    path = Path(document.storage_path)
    if document.kind != DocumentKind.FORM.value or not path.is_file():
        raise unavailable
    return FileResponse(path, media_type=document.mime_type, filename=document.original_name)


@router.get("/download/qr", response_class=Response)
def download_qr(token: str) -> Response:
    """Imagen PNG del QR que lleva al enlace de descarga, para el quiosco y el mantenedor.

    Solo verifica la firma: si el formato deja de serlo, el QR sigue dibujandose pero la
    descarga que abre ya no funciona.
    """
    try:
        download_service.read_token(token)
    except InvalidDownloadTokenError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El enlace no es válido o ya caducó.")
    return Response(content=_qr_png(download_service.url_for(token)), media_type="image/png")


# Despues de /download/qr: declarada antes, "download" se intentaria leer como un id.
@router.get("/{document_id}/qr", response_class=Response)
def public_url_qr(document_id: uuid.UUID, db: Session = Depends(get_db)) -> Response:
    """QR del enlace publico de un formato: no caduca, como el enlace al que apunta."""
    try:
        document = service.get_document(db, document_id)
    except DocumentNotFoundError:
        document = None
    if document is None or document.kind != DocumentKind.FORM.value or not document.public_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El formato no tiene enlace público.")
    return Response(content=_qr_png(document.public_url), media_type="image/png")


def _qr_png(url: str) -> bytes:
    buffer = io.BytesIO()
    # Escala grande y borde estandar: se escanea desde la pantalla de un quiosco.
    segno.make(url, error="m").save(buffer, kind="png", scale=10, border=4)
    return buffer.getvalue()


@router.get("/{document_id}", response_model=DocumentResponse, dependencies=[Depends(require_maintainer)])
def get_document(document_id: uuid.UUID, db: Session = Depends(get_db)) -> DocumentResponse:
    try:
        return service.get_document(db, document_id)
    except DocumentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado.")


@router.put("/{document_id}", response_model=DocumentResponse, dependencies=[Depends(require_maintainer)])
def update_document(
    document_id: uuid.UUID, payload: DocumentUpdate, db: Session = Depends(get_db)
) -> DocumentResponse:
    try:
        return service.update_document(db, document_id, payload)
    except DocumentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado.")
    except InvalidDocumentError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except VectorCleanupError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_maintainer)],
)
def delete_document(document_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    try:
        service.delete_document(db, document_id)
    except DocumentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado.")


@router.post(
    "/{document_id}/process",
    response_model=ProcessingResult,
    dependencies=[Depends(require_maintainer)],
)
def process_document(document_id: uuid.UUID, db: Session = Depends(get_db)) -> ProcessingResult:
    try:
        return processing_service.process_document(db, document_id)
    except DocumentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado.")
    except FileMissingError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="El archivo físico no existe."
        )
    except EmptyDocumentError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.post(
    "/{document_id}/index",
    response_model=IndexResult,
    dependencies=[Depends(require_maintainer)],
)
def index_document(document_id: uuid.UUID, db: Session = Depends(get_db)) -> IndexResult:
    try:
        return processing_service.index_document(db, document_id)
    except DocumentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado.")
    except FormNotIndexableError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except FileMissingError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="El archivo físico no existe."
        )
    except EmptyDocumentError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except IndexingError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.get(
    "/{document_id}/chunks",
    response_model=IndexedChunks,
    dependencies=[Depends(require_maintainer)],
)
def get_indexed_chunks(document_id: uuid.UUID, db: Session = Depends(get_db)) -> IndexedChunks:
    try:
        return processing_service.get_indexed_chunks(db, document_id)
    except DocumentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado.")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No fue posible consultar la base vectorial (¿Qdrant activo?).",
        )
