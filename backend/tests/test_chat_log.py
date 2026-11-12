import pytest

from app.services.chat_log_service import mask


@pytest.mark.parametrize(
    "text, hidden",
    [
        ("Mi cédula es 1144123456", "1144123456"),
        ("mi cedula es 1.144.123.456", "1.144.123.456"),
        ("escríbeme a juan.perez@usc.edu.co", "juan.perez@usc.edu.co"),
        ("mi celular es 315 678 9012", "315 678 9012"),
        ("llámame al +57 3156789012", "3156789012"),
        ("mi código estudiantil es 20201234", "20201234"),
    ],
)
def test_los_datos_personales_no_se_guardan(text, hidden):
    masked = mask(text)

    assert hidden not in masked
    assert "[" in masked


@pytest.mark.parametrize(
    "text",
    [
        "¿Cómo diligencio el formato R-GA002?",
        "Saqué 2.94 en el parcial, ¿puedo habilitar?",
        "¿Cuándo empiezan las clases en 2026?",
        "Tengo 18 créditos matriculados",
    ],
)
def test_lo_que_no_es_personal_se_conserva(text):
    assert mask(text) == text


def test_un_texto_vacio_queda_igual():
    assert mask(None) is None
    assert mask("") == ""
