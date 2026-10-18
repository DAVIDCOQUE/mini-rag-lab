import uuid
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

from app.main import app
from app.services import download_service

PNG = b"\x89PNG\r\n\x1a\n"

# Sin "with": no arranca el lifespan, asi que no necesita Ollama, Qdrant ni OCR.
client = TestClient(app)


def _path(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.path}?{parsed.query}"


def test_el_qr_de_un_enlace_valido_es_una_imagen_png():
    link = download_service.create_link(uuid.uuid4())

    response = client.get(_path(link.qr_url))

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(PNG)


def test_el_qr_lleva_el_mismo_token_que_la_descarga():
    link = download_service.create_link(uuid.uuid4())

    token_qr = parse_qs(urlparse(link.qr_url).query)["token"][0]
    token_descarga = parse_qs(urlparse(link.url).query)["token"][0]

    assert token_qr == token_descarga


def test_no_se_dibuja_el_qr_de_un_enlace_alterado():
    link = download_service.create_link(uuid.uuid4())

    response = client.get(_path(link.qr_url)[:-3] + "xyz")

    assert response.status_code == 404
