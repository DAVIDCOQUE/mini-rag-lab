from fastapi import APIRouter

from app.api.routes import chat, health
from app.core.config import settings

# Router raiz de la API. Aqui se agregan los routers de cada modulo.
# /health se sirve en la raiz; las rutas de negocio van bajo settings.API_PREFIX.
api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(chat.router, prefix=settings.API_PREFIX)
