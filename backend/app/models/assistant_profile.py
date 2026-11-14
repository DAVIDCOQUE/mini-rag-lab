import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class AssistantProfile(Base):
    """Identidad del asistente y datos de la institucion, editables desde el mantenedor.

    Una sola fila. Solo alimenta textos fijos (presentacion y a donde remitir):
    las respuestas sobre tramites siguen saliendo unicamente de los documentos.
    """

    __tablename__ = "assistant_profile"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    assistant_name: Mapped[str] = mapped_column(String(60))
    # FEMININE o MASCULINE: concordancia de "la asistente" / "el asistente".
    assistant_gender: Mapped[str] = mapped_column(String(20), default="FEMININE", server_default="FEMININE")
    institution_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    institution_short_name: Mapped[str | None] = mapped_column(String(30), nullable=True)
    city: Mapped[str | None] = mapped_column(String(80), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # A donde remitir cuando el asistente no tiene la respuesta.
    help_office: Mapped[str | None] = mapped_column(String(150), nullable=True)
    help_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    help_hours: Mapped[str | None] = mapped_column(String(150), nullable=True)
    help_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    help_email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
