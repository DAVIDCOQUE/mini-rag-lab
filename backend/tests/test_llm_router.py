import pytest

from app.rag import llm_router, llm_service
from app.rag.llm_service import LLMError
from app.rag.query_router import Route, RouteDecision
from app.schemas.chat import ChatTurn
from app.services import rag_service


def _responde(monkeypatch, salida: dict) -> list:
    """Sustituye la llamada a Ollama y devuelve los mensajes que se le enviaron."""
    enviados: list = []

    def falso(messages, schema, timeout):
        enviados.append(messages)
        return salida

    monkeypatch.setattr(llm_service, "chat_structured", falso)
    return enviados


def test_conversation_del_modelo_es_el_camino_smalltalk(monkeypatch):
    _responde(monkeypatch, {"reason": "pregunta por su nombre", "route": "conversation", "query": ""})

    decision = llm_router.decide("¿Cómo me llamo?", [ChatTurn(role="user", content="soy David")])

    assert decision.route is Route.SMALLTALK
    assert decision.router == "llm"
    assert decision.reason == "pregunta por su nombre"


def test_un_seguimiento_institucional_busca_con_la_pregunta_reescrita(monkeypatch):
    _responde(monkeypatch, {"reason": "-", "route": "institutional", "query": "¿Cuánto cuesta la matrícula?"})

    decision = llm_router.decide("¿Y cuánto cuesta?", [])

    assert decision.search_query == "¿Cuánto cuesta la matrícula?"


def test_sin_reescritura_se_busca_con_la_pregunta_original(monkeypatch):
    _responde(monkeypatch, {"reason": "-", "route": "institutional", "query": "  "})

    decision = llm_router.decide("¿Quién es el rector?", None)

    assert decision.search_query == "¿Quién es el rector?"


def test_una_ruta_desconocida_no_se_acepta(monkeypatch):
    _responde(monkeypatch, {"reason": "-", "route": "inventada", "query": ""})

    with pytest.raises(LLMError):
        llm_router.decide("hola", None)


def test_el_mensaje_va_separado_del_historial(monkeypatch):
    # Sin esta separacion, llama3.1:8b clasificaba casi todo como conversacion.
    enviados = _responde(monkeypatch, {"reason": "-", "route": "conversation", "query": ""})

    llm_router.decide("hola", None)

    contenido = enviados[0][1]["content"]
    assert "(sin historial)" in contenido
    assert contenido.endswith("MENSAJE A CLASIFICAR: hola")


def test_si_el_llm_falla_decide_el_router_de_embeddings(monkeypatch):
    def falla(question, history):
        raise LLMError("timeout")

    respaldo = RouteDecision(route=Route.GENERAL, search_query="x", router="embedding")
    monkeypatch.setattr(llm_router, "decide", falla)
    monkeypatch.setattr(rag_service.retriever.embedding_service, "embed_query", lambda text: [1.0])
    monkeypatch.setattr(rag_service.router, "classify", lambda vector: (respaldo.route, {}))

    decision = rag_service.route_query("¿Qué es una tesis?", None, mode="llm")

    assert decision.router == "embedding"
    assert decision.route is Route.GENERAL
