import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChatLogItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    conversation_id: str | None
    turn: int
    question: str
    answer: str
    route: str
    router: str | None
    search_query: str | None
    top_score: float | None
    no_answer: bool
    offered_forms: str | None
    delivered_forms: str | None
    prompt_code: str | None
    routing_ms: float | None
    retrieval_ms: float | None
    generation_ms: float | None
    total_ms: float


class ChatLogStats(BaseModel):
    total: int
    no_answer: int
    forms_delivered: int
    median_ms: float | None
    conversations: int
    by_route: dict[str, int]


class ChatLogPage(BaseModel):
    total: int
    items: list[ChatLogItem]
    stats: ChatLogStats
    retention_days: int
