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


class ChatResponse(BaseModel):
    question: str
    answer: str
    sources: list[ChatSource]
