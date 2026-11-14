import csv
import io
import logging
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.chat_log import ChatLog
from app.rag.prompt_builder import says_no_answer
from app.repositories import document_repository

logger = logging.getLogger("mini_rag_lab")

# Orden importante: el correo antes que los numeros, que tambien aparecen dentro de el.
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# Celulares y fijos de Colombia, con o sin +57 y separadores.
_PHONE = re.compile(r"(?:\+?57[\s-]?)?(?:\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}|\d{3}[\s-]?\d{4})\b")
# Cedulas y codigos estudiantiles: 6 o mas digitos seguidos (o con puntos de miles).
_ID_NUMBER = re.compile(r"\b\d{1,3}(?:\.\d{3}){1,3}\b|\b\d{6,}\b")


def mask(text: str | None) -> str | None:
    """Oculta correos, telefonos y numeros de documento antes de guardar el texto."""
    if not text:
        return text
    text = _EMAIL.sub("[correo]", text)
    # Una cedula de 10 digitos y un celular no se distinguen: misma etiqueta para ambos.
    text = _PHONE.sub("[numero]", text)
    return _ID_NUMBER.sub("[numero]", text)


def record(db: Session, question: str, history_len: int, conversation_id: str | None, outcome, total_ms: float) -> None:
    """Guarda el turno. Nunca rompe el chat: si falla, se registra y se sigue."""
    if not settings.CHAT_LOG_ENABLED:
        return
    try:
        # El texto de la oferta lleva el codigo del formato: se recupera de ahi.
        offered = [
            form.form_code
            for form in document_repository.list_forms(db)
            if form.form_code and form.form_code in outcome.answer
        ]
        delivered = [form.form_code for form, _ in outcome.forms if form.form_code]
        db.add(
            ChatLog(
                conversation_id=(conversation_id or None) and conversation_id[:64],
                turn=history_len // 2,
                question=mask(question),
                answer=mask(outcome.answer),
                route=outcome.route.value,
                router=outcome.router,
                search_query=mask(outcome.search_query),
                top_score=round(outcome.points[0].score, 3) if outcome.points else None,
                no_answer=says_no_answer(outcome.answer),
                offered_forms=",".join(code for code in offered if code not in delivered) or None,
                delivered_forms=",".join(delivered) or None,
                prompt_code=outcome.prompt_code,
                routing_ms=outcome.routing_ms,
                retrieval_ms=outcome.retrieval_ms,
                generation_ms=outcome.generation_ms,
                total_ms=round(total_ms, 1),
            )
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("No se pudo guardar el log de la conversacion: %s", exc)


def purge_expired(db: Session) -> int:
    """Borra los turnos mas viejos que CHAT_LOG_RETENTION_DAYS. Devuelve cuantos borro."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.CHAT_LOG_RETENTION_DAYS)
    result = db.execute(delete(ChatLog).where(ChatLog.created_at < cutoff))
    db.commit()
    if result.rowcount:
        logger.info("Log de conversaciones: %d turnos vencidos borrados.", result.rowcount)
    return result.rowcount


@dataclass
class LogFilters:
    route: str | None = None
    no_answer: bool | None = None
    text: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


def _where(filters: LogFilters) -> list:
    conditions = []
    if filters.route:
        conditions.append(ChatLog.route == filters.route)
    if filters.no_answer is not None:
        conditions.append(ChatLog.no_answer.is_(filters.no_answer))
    if filters.text:
        conditions.append(ChatLog.question.ilike(f"%{filters.text}%"))
    if filters.date_from:
        conditions.append(ChatLog.created_at >= filters.date_from)
    if filters.date_to:
        conditions.append(ChatLog.created_at < filters.date_to)
    return conditions


def list_logs(db: Session, filters: LogFilters, limit: int, offset: int) -> tuple[int, Sequence[ChatLog]]:
    conditions = _where(filters)
    total = db.execute(select(func.count()).select_from(ChatLog).where(*conditions)).scalar_one()
    rows = db.execute(
        select(ChatLog).where(*conditions).order_by(ChatLog.created_at.desc()).limit(limit).offset(offset)
    ).scalars().all()
    return total, rows


def stats(db: Session, filters: LogFilters) -> dict:
    """Totales para la cabecera de la pantalla, con los mismos filtros que la lista."""
    conditions = _where(filters)
    row = db.execute(
        select(
            func.count(),
            func.count().filter(ChatLog.no_answer.is_(True)),
            func.count().filter(ChatLog.delivered_forms.is_not(None)),
            func.percentile_cont(0.5).within_group(ChatLog.total_ms),
            func.count(func.distinct(ChatLog.conversation_id)),
        ).where(*conditions)
    ).one()
    by_route = dict(
        db.execute(select(ChatLog.route, func.count()).where(*conditions).group_by(ChatLog.route)).all()
    )
    return {
        "total": row[0],
        "no_answer": row[1],
        "forms_delivered": row[2],
        "median_ms": round(row[3], 1) if row[3] is not None else None,
        "conversations": row[4],
        "by_route": by_route,
    }


CSV_COLUMNS = [
    "created_at", "conversation_id", "turn", "question", "answer", "route", "router", "search_query",
    "top_score", "no_answer", "offered_forms", "delivered_forms", "prompt_code", "routing_ms",
    "retrieval_ms", "generation_ms", "total_ms",
]


def to_csv(rows: Sequence[ChatLog]) -> str:
    buffer = io.StringIO()
    # Punto y coma: Excel en espanol lo abre en columnas sin pasar por el asistente de importacion.
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(CSV_COLUMNS)
    for row in rows:
        writer.writerow([getattr(row, column) for column in CSV_COLUMNS])
    # BOM: sin el, Excel lee las tildes como si fuera Latin-1.
    return "﻿" + buffer.getvalue()
