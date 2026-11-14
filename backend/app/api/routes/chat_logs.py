from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import require_maintainer
from app.database.session import get_db
from app.schemas.chat_log import ChatLogPage, ChatLogStats
from app.services import chat_log_service as service
from app.services.chat_log_service import LogFilters

router = APIRouter(
    prefix="/chat-logs",
    tags=["chat-logs"],
    dependencies=[Depends(require_maintainer)],
)

# Tope del CSV: suficiente para la retencion por defecto sin cargar la tabla entera.
EXPORT_LIMIT = 20000


def _filters(
    route: str | None = None,
    no_answer: bool | None = None,
    q: str | None = Query(None, max_length=200),
    date_from: date | None = None,
    date_to: date | None = None,
) -> LogFilters:
    # date_to incluye el dia completo.
    return LogFilters(
        route=route,
        no_answer=no_answer,
        text=(q or "").strip() or None,
        date_from=datetime.combine(date_from, time.min, tzinfo=timezone.utc) if date_from else None,
        date_to=datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=timezone.utc) if date_to else None,
    )


@router.get("", response_model=ChatLogPage)
def list_chat_logs(
    filters: LogFilters = Depends(_filters),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> ChatLogPage:
    # La purga va aqui y al arrancar: sin tareas programadas, es cuando alguien mira.
    service.purge_expired(db)
    total, items = service.list_logs(db, filters, limit, offset)
    return ChatLogPage(
        total=total,
        items=items,
        stats=ChatLogStats(**service.stats(db, filters)),
        retention_days=settings.CHAT_LOG_RETENTION_DAYS,
    )


@router.get("/export", response_class=Response)
def export_chat_logs(filters: LogFilters = Depends(_filters), db: Session = Depends(get_db)) -> Response:
    _, rows = service.list_logs(db, filters, EXPORT_LIMIT, 0)
    filename = f"conversaciones-sara-{date.today().isoformat()}.csv"
    return Response(
        content=service.to_csv(rows),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
