import io
import uuid
from pathlib import Path

import segno

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.document import DocumentKind, DocumentResponse, DocumentUpdate
from app.schemas.processing import IndexedChunks, IndexResult, ProcessingResult
from app.services import document_service as service
from app.services import download_service
from app.services.download_service import InvalidDownloadTokenError
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


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def create_document(
    file: UploadFile = File(...),
    kind: DocumentKind = Form(DocumentKind.KNOWLEDGE),
    description: str | None = Form(None),
    db: Session = Depends(get_db),
) -> DocumentResponse:
    try:
        return service.create_document(db, file, kind, description)
    except InvalidDocumentError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db)) -> list[DocumentResponse]:
    return service.list_documents(db)


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
    buffer = io.BytesIO()
    # Escala grande y borde estandar: se escanea desde la pantalla de un quiosco.
    segno.make(download_service.url_for(token), error="m").save(buffer, kind="png", scale=10, border=4)
    return Response(content=buffer.getvalue(), media_type="image/png")


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: uuid.UUID, db: Session = Depends(get_db)) -> DocumentResponse:
    try:
        return service.get_document(db, document_id)
    except DocumentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado.")


@router.put("/{document_id}", response_model=DocumentResponse)
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


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    try:
        service.delete_document(db, document_id)
    except DocumentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado.")


@router.post("/{document_id}/process", response_model=ProcessingResult)
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


@router.post("/{document_id}/index", response_model=IndexResult)
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


@router.get("/{document_id}/chunks", response_model=IndexedChunks)
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
