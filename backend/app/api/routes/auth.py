from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    password: str = Field(min_length=1, max_length=256)


class LoginResponse(BaseModel):
    token: str
    expires_at: datetime


class AuthStatus(BaseModel):
    # False: el backend no tiene contrasena configurada y el mantenedor no pide login.
    enabled: bool


@router.get("/status", response_model=AuthStatus)
def auth_status() -> AuthStatus:
    return AuthStatus(enabled=auth_service.is_enabled())


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request) -> LoginResponse:
    if not auth_service.is_enabled():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El acceso con contraseña no está configurado.")
    client = request.client.host if request.client else "unknown"
    if not auth_service.verify_password(payload.password):
        # Solo cuentan los fallos: un administrador que entra bien no se bloquea.
        if not auth_service.login_limiter.allow(client):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Demasiados intentos. Espera un minuto.",
                headers={"Retry-After": "60"},
            )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Contraseña incorrecta.")
    token, expires_at = auth_service.create_token()
    return LoginResponse(token=token, expires_at=expires_at)
