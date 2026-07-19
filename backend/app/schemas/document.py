import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class DocumentStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    INDEXED = "INDEXED"
    ERROR = "ERROR"


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_name: str
    stored_name: str
    storage_path: str
    mime_type: str
    extension: str
    size_bytes: int
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime


class DocumentUpdate(BaseModel):
    """Solo informacion administrativa: no reemplaza el archivo fisico."""

    original_name: str | None = None
    status: DocumentStatus | None = None
