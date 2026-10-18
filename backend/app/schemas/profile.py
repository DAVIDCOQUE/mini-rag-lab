import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class AssistantGender(str, Enum):
    FEMININE = "FEMININE"
    MASCULINE = "MASCULINE"


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    assistant_name: str
    assistant_gender: AssistantGender
    institution_name: str | None
    institution_short_name: str | None
    city: str | None
    website: str | None
    help_office: str | None
    help_location: str | None
    help_hours: str | None
    help_phone: str | None
    help_email: str | None
    updated_at: datetime


class ProfileUpdate(BaseModel):
    """Campos a cambiar; un texto vacio deja el campo sin valor."""

    assistant_name: str | None = Field(default=None, max_length=60)
    assistant_gender: AssistantGender | None = None
    institution_name: str | None = Field(default=None, max_length=150)
    institution_short_name: str | None = Field(default=None, max_length=30)
    city: str | None = Field(default=None, max_length=80)
    website: str | None = Field(default=None, max_length=255)
    help_office: str | None = Field(default=None, max_length=150)
    help_location: str | None = Field(default=None, max_length=255)
    help_hours: str | None = Field(default=None, max_length=150)
    help_phone: str | None = Field(default=None, max_length=50)
    help_email: str | None = Field(default=None, max_length=150)
