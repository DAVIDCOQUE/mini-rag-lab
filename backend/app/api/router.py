from fastapi import APIRouter

from app.api.routes import health

# Router raiz de la API. Aqui se agregan los routers de cada modulo.
api_router = APIRouter()
api_router.include_router(health.router)
