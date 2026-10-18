import uuid
from urllib.parse import parse_qs, urlparse

import pytest

from app.core.config import settings
from app.services import download_service
from app.services.download_service import InvalidDownloadTokenError

AHORA = 1_800_000_000.0
DOC = uuid.UUID("11111111-2222-3333-4444-555555555555")


def _token(url: str) -> str:
    return parse_qs(urlparse(url).query)["token"][0]


def test_un_enlace_recien_creado_devuelve_su_documento():
    link = download_service.create_link(DOC, now=AHORA)

    assert download_service.read_token(_token(link.url), now=AHORA + 60) == DOC


def test_el_enlace_apunta_a_la_direccion_publica(monkeypatch):
    monkeypatch.setattr(settings, "PUBLIC_BASE_URL", "https://asistente.universidad.edu.co/")

    link = download_service.create_link(DOC, now=AHORA)

    assert link.url.startswith("https://asistente.universidad.edu.co/api/documents/download?token=")


def test_un_enlace_caducado_no_vale(monkeypatch):
    monkeypatch.setattr(settings, "DOWNLOAD_LINK_TTL_MINUTES", 15)
    token = _token(download_service.create_link(DOC, now=AHORA).url)

    with pytest.raises(InvalidDownloadTokenError):
        download_service.read_token(token, now=AHORA + 15 * 60 + 1)


def test_cambiar_el_documento_del_enlace_invalida_la_firma():
    token = _token(download_service.create_link(DOC, now=AHORA).url)
    _, firma = token.split(".")
    otro = download_service._encode(f"{uuid.uuid4()}:{int(AHORA) + 900}".encode())

    with pytest.raises(InvalidDownloadTokenError):
        download_service.read_token(f"{otro}.{firma}", now=AHORA)


def test_alargar_la_caducidad_invalida_la_firma():
    token = _token(download_service.create_link(DOC, now=AHORA).url)
    _, firma = token.split(".")
    eterno = download_service._encode(f"{DOC}:9999999999".encode())

    with pytest.raises(InvalidDownloadTokenError):
        download_service.read_token(f"{eterno}.{firma}", now=AHORA)


@pytest.mark.parametrize("basura", ["", "sin-punto", "a.b.c", "%%%.%%%"])
def test_un_token_mal_formado_no_revienta(basura):
    with pytest.raises(InvalidDownloadTokenError):
        download_service.read_token(basura, now=AHORA)
