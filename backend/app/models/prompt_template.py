import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, Uuid, false, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class PromptTemplate(Base):
    """Variante del prompt de sistema creada desde la UI.

    El prompt por defecto NO vive aqui: vive en prompt_builder.SYSTEM_PROMPT_TEMPLATE,
    versionado en git. Esta tabla solo guarda los experimentos del usuario, de modo que
    una base vacia sigue dando el comportamiento revisable del repositorio.
    """

    __tablename__ = "prompt_templates"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # Identificador estable: es lo que las peticiones envian para pedir esta variante.
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    # Texto de las instrucciones. Admite el marcador {no_answer}, que se sustituye por
    # la frase de fallback del sistema al construir el prompt final.
    body: Mapped[str] = mapped_column(Text)
    # Como maximo una activa: es la que usa el chat cuando nadie pide otra.
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
