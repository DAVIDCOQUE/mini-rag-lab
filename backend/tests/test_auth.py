import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import auth_service
from app.services.auth_service import InvalidTokenError, RateLimiter

# Sin "with": no arranca el lifespan, asi que no necesita Ollama, Qdrant ni OCR.
client = TestClient(app)


@pytest.fixture
def password(monkeypatch):
    # Pocas iteraciones: el hash real tarda ~0,5 s a proposito.
    monkeypatch.setattr(auth_service.settings, "ADMIN_PASSWORD_HASH", auth_service.hash_password("clave-segura-1", 1000))
    return "clave-segura-1"


def test_la_contrasena_correcta_se_verifica_y_la_incorrecta_no(password):
    assert auth_service.verify_password(password)
    assert not auth_service.verify_password("otra")


def test_un_hash_mal_formado_no_deja_entrar():
    assert not auth_service.verify_password("x", "basura")


def test_un_token_alterado_o_caducado_se_rechaza():
    token, _ = auth_service.create_token(now=1000)
    auth_service.verify_token(token, now=1000)
    with pytest.raises(InvalidTokenError):
        auth_service.verify_token(token[:-2] + "xx", now=1000)
    with pytest.raises(InvalidTokenError):
        auth_service.verify_token(token, now=1000 + 9 * 3600)


def test_sin_sesion_el_mantenedor_responde_401(password):
    assert client.get("/api/profile").status_code == 401
    assert client.get("/api/chat-logs").status_code == 401
    assert client.delete("/api/documents/00000000-0000-0000-0000-000000000000").status_code == 401


def test_el_login_correcto_entrega_un_token_que_abre_el_mantenedor(password):
    response = client.post("/api/auth/login", json={"password": password})
    assert response.status_code == 200
    token = response.json()["token"]

    # 404: paso la autenticacion y llego a la ruta, que no encuentra el documento.
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/documents/00000000-0000-0000-0000-000000000000", headers=headers).status_code == 404


def test_el_login_incorrecto_responde_401(password):
    assert client.post("/api/auth/login", json={"password": "mala"}).status_code == 401


def test_las_descargas_publicas_no_piden_sesion(password):
    # 404 y no 401: el enlace no es valido, pero la ruta no exige login.
    assert client.get("/api/documents/download?token=abc").status_code == 404
    assert client.get("/api/documents/00000000-0000-0000-0000-000000000000/qr").status_code == 404


def test_sin_contrasena_configurada_el_mantenedor_queda_abierto(monkeypatch):
    monkeypatch.setattr(auth_service.settings, "ADMIN_PASSWORD_HASH", "")
    assert client.get("/api/auth/status").json() == {"enabled": False}


def test_el_limite_corta_la_rafaga_y_se_recupera_al_minuto():
    limiter = RateLimiter(per_minute=3)
    assert all(limiter.allow("ip", now=0) for _ in range(3))
    assert not limiter.allow("ip", now=1)
    assert limiter.allow("otra-ip", now=1)
    assert limiter.allow("ip", now=61)


def test_con_clave_de_quiosco_el_chat_la_exige(monkeypatch):
    monkeypatch.setattr(auth_service.settings, "KIOSK_API_KEY", "kiosco-123")
    response = client.post("/api/chat", json={"message": "hola"}, headers={"X-Kiosk-Key": "mala"})
    assert response.status_code == 401
    assert auth_service.kiosk_key_matches("kiosco-123")
