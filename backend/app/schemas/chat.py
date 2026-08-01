from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class ChatSource(BaseModel):
    filename: str
    score: float
    chunk: str


class ChatResponse(BaseModel):
    question: str
    answer: str
    sources: list[ChatSource]
