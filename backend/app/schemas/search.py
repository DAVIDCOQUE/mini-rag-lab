import uuid

from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    limit: int = 5


class SearchResultItem(BaseModel):
    document_id: uuid.UUID
    page: int
    chunk_index: int
    content: str
    score: float


class SearchResponse(BaseModel):
    query: str
    total: int
    results: list[SearchResultItem]
