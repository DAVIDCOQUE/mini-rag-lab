import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# Minusculas, digitos y guiones: el code viaja en la URL y en cada peticion.
CODE_PATTERN = r"^[a-z0-9][a-z0-9-]{1,63}$"


class PromptTemplateCreate(BaseModel):
    code: str = Field(pattern=CODE_PATTERN)
    name: str = Field(min_length=2, max_length=120)
    body: str = Field(min_length=20)


class PromptTemplateUpdate(BaseModel):
    """El code no se edita: es la referencia estable que usan las peticiones."""

    name: str | None = Field(default=None, min_length=2, max_length=120)
    body: str | None = Field(default=None, min_length=20)


class PromptTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    body: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class DefaultPrompt(BaseModel):
    """Prompt del repositorio. Solo lectura: se muestra como referencia para crear variantes."""

    code: str
    name: str
    body: str
    no_answer_placeholder: str
    no_answer_message: str
