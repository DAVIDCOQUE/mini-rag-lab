import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, Uuid, false, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ChatLog(Base):
    """Un turno de /chat: que se pregunto, que se respondio y como se resolvio.

    question, answer y search_query se guardan enmascarados (chat_log_service.mask) y se
    borran pasados CHAT_LOG_RETENTION_DAYS.
    """

    __tablename__ = "chat_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    # Lo envia el cliente si quiere agrupar turnos; el backend sigue sin guardar estado.
    conversation_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    # 0 = primer mensaje de la conversacion.
    turn: Mapped[int] = mapped_column(Integer, default=0)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    route: Mapped[str] = mapped_column(String(20), index=True)
    router: Mapped[str | None] = mapped_column(String(20), nullable=True)
    search_query: Mapped[str | None] = mapped_column(Text, nullable=True)
    top_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    # El asistente dijo que no sabia: es lo primero que conviene revisar.
    no_answer: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false(), index=True)
    # Codigos separados por coma (R-GA002,R-GA004).
    offered_forms: Mapped[str | None] = mapped_column(String(255), nullable=True)
    delivered_forms: Mapped[str | None] = mapped_column(String(255), nullable=True)
    prompt_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    routing_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    retrieval_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    generation_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_ms: Mapped[float] = mapped_column(Float)
