from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assistant_profile import AssistantProfile


def get(db: Session) -> AssistantProfile | None:
    """El perfil: la tabla tiene como mucho una fila."""
    return db.execute(select(AssistantProfile).limit(1)).scalar_one_or_none()


def create(db: Session, profile: AssistantProfile) -> AssistantProfile:
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def update(db: Session, profile: AssistantProfile) -> AssistantProfile:
    db.commit()
    db.refresh(profile)
    return profile
