import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.documents import ocr
from app.database.session import SessionLocal
from app.services import chat_log_service, rag_service

configure_logging()
logger = logging.getLogger("mini_rag_lab")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Cargar los modelos al arrancar y no en la primera consulta: el coste se paga
    # durante el despliegue, no en la cara del primer usuario.
    rag_service.warm_up()
    ocr.warm_up()
    _purge_chat_logs()
    yield


def _purge_chat_logs() -> None:
    """Retencion del log de conversaciones; best-effort, como el calentamiento."""
    try:
        with SessionLocal() as db:
            chat_log_service.purge_expired(db)
    except Exception as exc:
        logging.getLogger("mini_rag_lab").warning("No se pudo purgar el log de conversaciones: %s", exc)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    contact={"name": "@DAVIDCOQUE", "url": "https://github.com/DAVIDCOQUE"},
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# CORS para permitir el consumo desde el frontend Angular.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Registra metodo, ruta, codigo HTTP y tiempo de respuesta de cada peticion."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %d (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
