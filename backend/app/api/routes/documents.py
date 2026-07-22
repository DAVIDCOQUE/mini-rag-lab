import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.document import DocumentResponse, DocumentUpdate
from app.schemas.processing import ProcessingResult
from app.services import document_service as service
from app.services.document_processing_service import (
    DocumentProcessingService,
    EmptyDocumentError,
    FileMissingError,
)
from app.services.document_service import DocumentNotFoundError, InvalidDocumentError

router = APIRouter(prefix="/documents", tags=["documents"])

processing_service = DocumentProcessingService()


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def create_document(file: UploadFile = File(...), db: Session = Depends(get_db)) -> DocumentResponse:
    try:
        return service.create_document(db, file)
    except InvalidDocumentError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db)) -> list[DocumentResponse]:
    return service.list_documents(db)


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
