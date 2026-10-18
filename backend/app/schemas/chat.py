import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    # Turnos previos de la conversacion en curso. El servidor no guarda nada entre
    # peticiones: borrar la conversacion es responsabilidad del cliente (el quiosco).
    history: list[ChatTurn] = Field(default_factory=list)


class ChatSource(BaseModel):
    filename: str
    score: float
    chunk: str


class ChatDownload(BaseModel):
    """Formato que el estudiante puede llevarse: el quiosco convierte url en un QR."""

    document_id: uuid.UUID
    filename: str
    url: str
    # Imagen PNG del QR de url, generada por el backend: el cliente solo la muestra.
    qr_url: str
    expires_at: datetime


class ChatResponse(BaseModel):
    question: str
    answer: str
    sources: list[ChatSource]
    downloads: list[ChatDownload] = Field(default_factory=list)
