import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Document(Base):
    """Documento subido por el usuario. En esta fase solo se gestiona el archivo, sin procesarlo."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    original_name: Mapped[str] = mapped_column(String(255))
    stored_name: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(512))
    mime_type: Mapped[str] = mapped_column(String(127))
    extension: Mapped[str] = mapped_column(String(16))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    # Valores posibles: PENDING, PROCESSING, INDEXED, ERROR.
    status: Mapped[str] = mapped_column(String(20), default="PENDING", server_default="PENDING")
    # KNOWLEDGE: se indexa y el asistente responde con el. FORM: formato en blanco que el
    # estudiante descarga por QR; nunca se indexa, porque sus campos vacios solo meterian
    # ruido en la busqueda.
    kind: Mapped[str] = mapped_column(String(20), default="KNOWLEDGE", server_default="KNOWLEDGE")
    # Para que sirve el formato, escrito por el administrador. Es lo que se compara con
    # la pregunta para decidir si ofrecerlo: el PDF de un formato no dice para que es.
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
