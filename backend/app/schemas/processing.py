import uuid

from pydantic import BaseModel


class ChunkResponse(BaseModel):
    index: int
    page: int
    characters: int
    content: str


class ProcessingResult(BaseModel):
    document_id: uuid.UUID
    total_pages: int
    total_characters: int
    total_chunks: int
    chunks: list[ChunkResponse]
