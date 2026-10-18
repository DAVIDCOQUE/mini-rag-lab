import base64
import hashlib
import hmac
import secrets
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from app.core.config import settings

# Sin secreto configurado se usa uno por proceso: los enlaces caducan en minutos, asi
# que perderlos al reiniciar no afecta a nadie.
_SECRET = (settings.DOWNLOAD_SECRET or secrets.token_hex(32)).encode()


class InvalidDownloadTokenError(Exception):
    """El enlace esta alterado, mal formado o caducado."""


@dataclass
class DownloadLink:
    url: str
    qr_url: str
    expires_at: datetime


def create_link(document_id: uuid.UUID, now: float | None = None) -> DownloadLink:
    """Enlace temporal y firmado para descargar el documento desde el celular."""
    expires = int((now if now is not None else time.time()) + settings.DOWNLOAD_LINK_TTL_MINUTES * 60)
    payload = f"{document_id}:{expires}"
    token = f"{_encode(payload.encode())}.{_encode(_sign(payload))}"
    return DownloadLink(
        url=url_for(token),
        qr_url=f"{_base()}/documents/download/qr?token={token}",
        expires_at=datetime.fromtimestamp(expires, tz=timezone.utc),
    )


def url_for(token: str) -> str:
    """Enlace publico de descarga que va dentro del QR."""
    return f"{_base()}/documents/download?token={token}"


def _base() -> str:
    return f"{settings.PUBLIC_BASE_URL.rstrip('/')}{settings.API_PREFIX}"


def read_token(token: str, now: float | None = None) -> uuid.UUID:
    """Id del documento si la firma es valida y el enlace no ha caducado."""
    try:
        encoded_payload, encoded_signature = token.split(".")
        payload = _decode(encoded_payload).decode()
        signature = _decode(encoded_signature)
        document_id, expires = payload.split(":")
    except ValueError as exc:
        raise InvalidDownloadTokenError from exc

    # compare_digest: comparar en tiempo constante no deja deducir la firma midiendo tiempos.
    if not hmac.compare_digest(signature, _sign(payload)):
        raise InvalidDownloadTokenError
    if int(expires) < (now if now is not None else time.time()):
        raise InvalidDownloadTokenError
    try:
        return uuid.UUID(document_id)
    except ValueError as exc:
        raise InvalidDownloadTokenError from exc


def _sign(payload: str) -> bytes:
    return hmac.new(_SECRET, payload.encode(), hashlib.sha256).digest()


def _encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _decode(text: str) -> bytes:
    try:
        return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))
    except (ValueError, base64.binascii.Error) as exc:
        raise ValueError from exc
