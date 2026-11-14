import base64
import hashlib
import hmac
import secrets
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from threading import Lock

from app.core.config import settings

# Sin secreto configurado se usa uno por proceso: reiniciar el backend cierra las sesiones.
_SECRET = (settings.AUTH_SECRET or secrets.token_hex(32)).encode()

PBKDF2_ITERATIONS = 600_000


class InvalidTokenError(Exception):
    """La sesion esta alterada, mal formada o caducada."""


def is_enabled() -> bool:
    return bool(settings.ADMIN_PASSWORD_HASH)


# --- Contrasena: PBKDF2 de la libreria estandar, sin dependencias nuevas ---


def hash_password(password: str, iterations: int = PBKDF2_ITERATIONS) -> str:
    """'pbkdf2_sha256$iteraciones$sal$hash', listo para ADMIN_PASSWORD_HASH."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return f"pbkdf2_sha256${iterations}${_encode(salt)}${_encode(digest)}"


def verify_password(password: str, stored: str | None = None) -> bool:
    stored = stored if stored is not None else settings.ADMIN_PASSWORD_HASH
    try:
        algorithm, iterations, salt, expected = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), _decode(salt), int(iterations))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest, _decode(expected))


# --- Sesion: token firmado con HMAC, mismo esquema que los enlaces de descarga ---


def create_token(now: float | None = None) -> tuple[str, datetime]:
    expires = int((now if now is not None else time.time()) + settings.AUTH_TOKEN_TTL_HOURS * 3600)
    payload = f"admin:{expires}"
    token = f"{_encode(payload.encode())}.{_encode(_sign(payload))}"
    return token, datetime.fromtimestamp(expires, tz=timezone.utc)


def verify_token(token: str, now: float | None = None) -> None:
    try:
        encoded_payload, encoded_signature = token.split(".")
        payload = _decode(encoded_payload).decode()
        signature = _decode(encoded_signature)
        role, expires = payload.split(":")
    except ValueError as exc:
        raise InvalidTokenError from exc
    # compare_digest: comparar en tiempo constante no deja deducir la firma midiendo tiempos.
    if role != "admin" or not hmac.compare_digest(signature, _sign(payload)):
        raise InvalidTokenError
    if int(expires) < (now if now is not None else time.time()):
        raise InvalidTokenError


def kiosk_key_matches(key: str | None) -> bool:
    return bool(settings.KIOSK_API_KEY) and hmac.compare_digest((key or "").encode(), settings.KIOSK_API_KEY.encode())


# --- Limite de peticiones en memoria: un solo proceso de uvicorn, sin Redis ---


class RateLimiter:
    """Ventana deslizante de 60 s por clave (la IP del cliente)."""

    def __init__(self, per_minute: int) -> None:
        self.per_minute = per_minute
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str, now: float | None = None) -> bool:
        now = now if now is not None else time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] >= 60:
                hits.popleft()
            if len(hits) >= self.per_minute:
                return False
            hits.append(now)
            return True


chat_limiter = RateLimiter(settings.CHAT_RATE_LIMIT_PER_MINUTE)

# Intentos de login fallidos por IP: frena la fuerza bruta contra la contrasena compartida.
login_limiter = RateLimiter(10)


def _sign(payload: str) -> bytes:
    return hmac.new(_SECRET, payload.encode(), hashlib.sha256).digest()


def _encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _decode(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))
