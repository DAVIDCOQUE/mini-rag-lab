import uuid

import pytest

from app.api.routes.chat import _downloads
from app.models.document import Document
from app.services import document_service, onedrive_service
from app.services.document_service import InvalidDocumentError
from app.services.onedrive_service import CloudStorageError


def _form(public_url: str | None) -> Document:
    return Document(id=uuid.uuid4(), original_name="formato.pdf", kind="FORM", public_url=public_url)


def test_un_formato_con_enlace_publico_entrega_ese_enlace_sin_caducidad():
    form = _form("https://1drv.ms/b/s!abc")

    [download] = _downloads([(form, 1.0)])

    assert download.url == "https://1drv.ms/b/s!abc"
    assert download.qr_url.endswith(f"/documents/{form.id}/qr")
    assert download.expires_at is None


def test_un_formato_sin_enlace_publico_sigue_usando_el_enlace_firmado():
    form = _form(None)

    [download] = _downloads([(form, 1.0)])

    assert "/documents/download?token=" in download.url
    assert download.expires_at is not None


@pytest.mark.parametrize("url", ["", "   ", None])
def test_un_enlace_vacio_se_guarda_como_none(url):
    assert document_service._clean_public_url(url) is None


@pytest.mark.parametrize("url", ["javascript:alert(1)", "1drv.ms/b/abc", "ftp://x/y.pdf"])
def test_solo_se_aceptan_enlaces_http(url):
    with pytest.raises(InvalidDocumentError):
        document_service._clean_public_url(url)


def test_sin_configurar_onedrive_la_subida_falla_con_un_mensaje_claro(monkeypatch):
    monkeypatch.setattr(onedrive_service.settings, "ONEDRIVE_MODE", "")

    assert onedrive_service.is_enabled() is False
    with pytest.raises(CloudStorageError):
        onedrive_service.upload_form("formato.pdf", b"%PDF")
