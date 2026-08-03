from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.prompt_template import PromptTemplate


def create(db: Session, template: PromptTemplate) -> PromptTemplate:
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def list_all(db: Session) -> Sequence[PromptTemplate]:
    """Variantes ordenadas por fecha de creacion ascendente: el orden en que se probaron."""
    stmt = select(PromptTemplate).order_by(PromptTemplate.created_at)
    return db.execute(stmt).scalars().all()


def get_by_code(db: Session, code: str) -> PromptTemplate | None:
    stmt = select(PromptTemplate).where(PromptTemplate.code == code)
    return db.execute(stmt).scalar_one_or_none()


def get_active(db: Session) -> PromptTemplate | None:
    stmt = select(PromptTemplate).where(PromptTemplate.is_active.is_(True))
    return db.execute(stmt).scalars().first()


def update(db: Session, template: PromptTemplate) -> PromptTemplate:
    db.commit()
    db.refresh(template)
    return template


def delete(db: Session, template: PromptTemplate) -> None:
    db.delete(template)
    db.commit()


def deactivate_all(db: Session) -> None:
    """Apaga la activa sin hacer commit: quien activa decide cuando cerrar la transaccion."""
    stmt = select(PromptTemplate).where(PromptTemplate.is_active.is_(True))
    for template in db.execute(stmt).scalars().all():
        template.is_active = False
