from fastapi import APIRouter, Depends

from app.api.dependencies import require_admin
from app.api.routes import auth, chat, chat_logs, documents, health, profile, prompts, search
from app.core.config import settings

# Router raiz de la API. Aqui se agregan los routers de cada modulo.
# /health se sirve en la raiz; las rutas de negocio van bajo settings.API_PREFIX.
# Publicas: /health, /auth, /chat y las descargas de formatos (el quiosco y los celulares).
# Todo lo demas es del mantenedor y exige sesion; documents lo protege ruta por ruta
# porque mezcla ambas.
admin = [Depends(require_admin)]

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix=settings.API_PREFIX)
api_router.include_router(chat.router, prefix=settings.API_PREFIX)
api_router.include_router(chat_logs.router, prefix=settings.API_PREFIX, dependencies=admin)
api_router.include_router(documents.router, prefix=settings.API_PREFIX)
api_router.include_router(prompts.router, prefix=settings.API_PREFIX, dependencies=admin)
api_router.include_router(profile.router, prefix=settings.API_PREFIX, dependencies=admin)
api_router.include_router(search.router, prefix=settings.API_PREFIX, dependencies=admin)
