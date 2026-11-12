from app.rag.query_router import Route, RouteDecision
from app.services import rag_service


def _general(question: str) -> RouteDecision:
    return RouteDecision(route=Route.GENERAL, search_query=question, router="llm")


def test_un_termino_del_reglamento_marcado_como_general_se_busca_en_los_documentos():
    decision = rag_service._keep_institutional_terms(_general("¿Qué es una prueba de validación?"), "¿Qué es una prueba de validación?")

    assert decision.route is Route.INSTITUTIONAL
    # Si la guia no lo cubre, se explica como concepto con aviso, no se niega.
    assert decision.is_concept is True


def test_un_tema_general_sigue_siendo_general():
    decision = rag_service._keep_institutional_terms(_general("¿Qué es una tesis?"), "¿Qué es una tesis?")

    assert decision.route is Route.GENERAL
