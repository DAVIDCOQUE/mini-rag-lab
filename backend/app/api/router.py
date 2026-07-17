from fastapi import APIRouter

from app.api.routes import health

# Router raiz de la API. Aqui se agregan los routers de cada modulo.
# /health se sirve en la raiz; las rutas de negocio futuras iran bajo settings.API_PREFIX.
api_router = APIRouter()
api_router.include_router(health.router)
