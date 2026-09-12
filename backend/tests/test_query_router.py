import pytest

from app.core.config import settings
from app.rag.query_router import QueryRouter, Route, _cosine


def _router_con_centroides_controlados() -> QueryRouter:
    """Router con centroides inyectados, para no depender de Ollama.

    Son una base ortonormal: asi la similitud con cada camino es directamente la
    componente correspondiente del vector de consulta y el test fija los scores.
    """
    router = QueryRouter()
    router._centroids = {
        Route.INSTITUTIONAL: [1.0, 0.0, 0.0, 0.0],
        Route.GENERAL: [0.0, 1.0, 0.0, 0.0],
        Route.SMALLTALK: [0.0, 0.0, 1.0, 0.0],
        Route.OFF_TOPIC: [0.0, 0.0, 0.0, 1.0],
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
