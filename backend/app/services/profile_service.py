from sqlalchemy.orm import Session

from app.models.assistant_profile import AssistantProfile
from app.repositories import assistant_profile_repository as repository
from app.schemas.profile import ProfileUpdate

DEFAULT_ASSISTANT_NAME = "Sara"


class InvalidProfileError(Exception):
    """El perfil quedaria sin nombre de asistente."""


def get_profile(db: Session) -> AssistantProfile:
    """El perfil guardado; si aun no existe se crea con valores genericos."""
    profile = repository.get(db)
    if profile is None:
        profile = repository.create(db, _default())
    return profile


def current(db: Session | None) -> AssistantProfile:
    """Perfil para construir respuestas. Sin sesion (pruebas, scripts) usa el generico."""
    return get_profile(db) if db is not None else _default()


def update_profile(db: Session, payload: ProfileUpdate) -> AssistantProfile:
    profile = get_profile(db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        if hasattr(value, "value"):
            value = value.value
        elif isinstance(value, str):
            value = value.strip() or None
        setattr(profile, field, value)
    if not profile.assistant_name:
        db.rollback()
        raise InvalidProfileError("El asistente necesita un nombre.")
    return repository.update(db, profile)


def _default() -> AssistantProfile:
    return AssistantProfile(assistant_name=DEFAULT_ASSISTANT_NAME, assistant_gender="FEMININE")
