import pytest

from app.core.config import settings
from app.rag.query_router import QueryRouter, Route, _cosine, _nearest_mean, expand_follow_up
from app.schemas.chat import ChatTurn


def _router_con_centroides_controlados() -> QueryRouter:
    """Router con un ejemplo inyectado por camino, para no depender de Ollama.

    Son una base ortonormal: asi la similitud con cada camino es directamente la
    componente correspondiente del vector de consulta y el test fija los scores.
    """
    router = QueryRouter()
    router._examples = {
        Route.INSTITUTIONAL: [[1.0, 0.0, 0.0, 0.0]],
        Route.GENERAL: [[0.0, 1.0, 0.0, 0.0]],
        Route.SMALLTALK: [[0.0, 0.0, 1.0, 0.0]],
        Route.OFF_TOPIC: [[0.0, 0.0, 0.0, 1.0]],
    }
    return router


def test_cosine_de_vectores_identicos_es_uno():
    assert _cosine([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0)


def test_cosine_de_vectores_ortogonales_es_cero():
    assert _cosine([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_cosine_con_vector_nulo_no_divide_por_cero():
    assert _cosine([0.0, 0.0], [1.0, 0.0]) == 0.0


def test_institucional_gana_cuando_es_el_mas_parecido():
    ruta, scores = _router_con_centroides_controlados().classify([1.0, 0.0, 0.0, 0.0])

    assert ruta is Route.INSTITUTIONAL
    assert scores["institutional"] == pytest.approx(1.0)


def test_otro_camino_se_lleva_la_consulta_si_saca_ventaja_suficiente(monkeypatch):
    monkeypatch.setattr(settings, "ROUTER_SAFETY_MARGIN", 0.05)

    ruta, _ = _router_con_centroides_controlados().classify([0.1, 0.0, 0.99, 0.0])

    assert ruta is Route.SMALLTALK


def test_una_ventaja_ajustada_se_resuelve_a_favor_de_buscar(monkeypatch):
    # Responder de memoria sobre la institucion es el peor fallo posible, asi que
    # ante la duda se prefiere pagar la recuperacion.
    monkeypatch.setattr(settings, "ROUTER_SAFETY_MARGIN", 0.05)

    ruta, scores = _router_con_centroides_controlados().classify([0.70, 0.0, 0.72, 0.0])

    assert scores["smalltalk"] > scores["institutional"]  # smalltalk gana por score...
    assert ruta is Route.INSTITUTIONAL  # ...pero no por encima del margen


def test_el_margen_se_puede_desactivar_bajandolo_a_cero(monkeypatch):
    monkeypatch.setattr(settings, "ROUTER_SAFETY_MARGIN", 0.0)

    ruta, _ = _router_con_centroides_controlados().classify([0.70, 0.0, 0.72, 0.0])

    assert ruta is Route.SMALLTALK


def test_se_compara_con_los_ejemplos_mas_parecidos_y_no_con_el_promedio():
    # Un grupo con un ejemplo identico y otros lejanos: el promedio de todos lo
    # diluiria; los mas parecidos lo conservan.
    grupo = [[1.0, 0.0], [1.0, 0.0], [1.0, 0.0], [0.0, 1.0], [0.0, 1.0], [0.0, 1.0]]

    assert _nearest_mean([1.0, 0.0], grupo) == pytest.approx(1.0)


def test_off_topic_sin_ventaja_clara_cede_al_segundo_camino(monkeypatch):
    monkeypatch.setattr(settings, "ROUTER_OFF_TOPIC_MARGIN", 0.05)
    monkeypatch.setattr(settings, "ROUTER_SAFETY_MARGIN", 0.0)

    ruta, scores = _router_con_centroides_controlados().classify([0.0, 0.0, 0.70, 0.72])

    assert scores["off_topic"] > scores["smalltalk"]
    assert ruta is Route.SMALLTALK


def test_off_topic_con_ventaja_clara_se_queda(monkeypatch):
    monkeypatch.setattr(settings, "ROUTER_OFF_TOPIC_MARGIN", 0.05)

    ruta, _ = _router_con_centroides_controlados().classify([0.0, 0.0, 0.1, 0.99])

    assert ruta is Route.OFF_TOPIC


_HISTORIAL = [
    ChatTurn(role="user", content="¿Cuál es el procedimiento para la matrícula?"),
    ChatTurn(role="assistant", content="Se hace en línea."),
]


@pytest.mark.parametrize("mensaje", ["¿Y cuánto cuesta?", "y donde lo hago", "¿Eso hasta cuándo?"])
def test_un_seguimiento_lleva_delante_la_pregunta_anterior(mensaje):
    expandido = expand_follow_up(mensaje, _HISTORIAL)

    assert expandido == f"¿Cuál es el procedimiento para la matrícula? {mensaje}"


@pytest.mark.parametrize("mensaje", ["Muchas gracias, eso era todo", "¿Quién es el rector?"])
def test_lo_que_no_es_seguimiento_no_se_toca(mensaje):
    assert expand_follow_up(mensaje, _HISTORIAL) == mensaje


def test_sin_historial_no_hay_seguimiento():
    assert expand_follow_up("¿Y cuánto cuesta?", None) == "¿Y cuánto cuesta?"
