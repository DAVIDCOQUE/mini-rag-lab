from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Engine preparado para PostgreSQL. pool_pre_ping evita conexiones muertas.
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, echo=settings.DEBUG)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    """Dependencia FastAPI: entrega una sesion por request y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
