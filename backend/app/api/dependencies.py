from fastapi import Header, HTTPException, Request, status

from app.services import auth_service
from app.services.auth_service import InvalidTokenError


def _bearer(authorization: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None


def _has_admin_session(authorization: str | None) -> bool:
    token = _bearer(authorization)
    if not token:
        return False
    try:
        auth_service.verify_token(token)
    except InvalidTokenError:
        return False
    return True


def require_admin(authorization: str | None = Header(default=None)) -> None:
    """Rutas del mantenedor. Sin ADMIN_PASSWORD_HASH configurado quedan abiertas (desarrollo)."""
    if not auth_service.is_enabled():
        return
    if not _has_admin_session(authorization):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inicia sesión en el mantenedor.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def guard_chat(
    request: Request,
    authorization: str | None = Header(default=None),
    x_kiosk_key: str | None = Header(default=None),
) -> None:
    """/chat: clave del quiosco (si esta definida) o sesion del mantenedor, y limite por IP."""
    if auth_service.settings.KIOSK_API_KEY and not (
        auth_service.kiosk_key_matches(x_kiosk_key) or _has_admin_session(authorization)
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Clave del quiosco no válida.")
    client = request.client.host if request.client else "unknown"
    if not auth_service.chat_limiter.allow(client):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados mensajes seguidos. Espera un momento.",
            headers={"Retry-After": "60"},
        )
