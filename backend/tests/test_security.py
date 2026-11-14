from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core.config import settings
from app.main import app

PASSWORD = "test-maintainer-password-2026"
client = TestClient(app)


@pytest.fixture
def configured_password(monkeypatch):
    monkeypatch.setattr(settings, "MAINTAINER_PASSWORD", SecretStr(PASSWORD))


def test_missing_password_configuration_fails_closed(monkeypatch):
    monkeypatch.setattr(settings, "MAINTAINER_PASSWORD", SecretStr(""))

    response = client.get("/api/auth/verify")

    assert response.status_code == 503


def test_missing_credentials_are_rejected(configured_password):
    response = client.get("/api/auth/verify")

    assert response.status_code == 401


def test_invalid_credentials_are_rejected(configured_password):
    response = client.get("/api/auth/verify", auth=("mantenedor", "incorrecta"))

    assert response.status_code == 401


def test_valid_credentials_are_accepted(configured_password):
    response = client.get("/api/auth/verify", auth=("mantenedor", PASSWORD))

    assert response.status_code == 200
    assert response.json() == {"authenticated": True}


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/documents"),
        ("delete", f"/api/documents/{uuid4()}"),
    ],
)
def test_document_administration_requires_authentication(
    configured_password, method, path
):
    response = getattr(client, method)(path)

    assert response.status_code == 401
