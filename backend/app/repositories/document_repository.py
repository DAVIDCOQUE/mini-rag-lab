import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document


def create(db: Session, document: Document) -> Document:
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def list_all(db: Session) -> Sequence[Document]:
    """Todos los documentos ordenados por fecha de creacion descendente."""
    stmt = select(Document).order_by(Document.created_at.desc())
    return db.execute(stmt).scalars().all()


def get(db: Session, document_id: uuid.UUID) -> Document | None:
    return db.get(Document, document_id)


def update(db: Session, document: Document) -> Document:
    db.commit()
    db.refresh(document)
    return document


def delete(db: Session, document: Document) -> None:
    db.delete(document)
    db.commit()
