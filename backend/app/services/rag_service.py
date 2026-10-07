import logging
import time
from collections.abc import Sequence
from dataclasses import dataclass, field

from qdrant_client.models import ScoredPoint
from sqlalchemy.orm import Session

from app.core.config import settings
from app.rag import llm_router
from app.rag.llm_service import LLMError, chat
from app.rag.prompt_builder import (
    FIRST_TURN_GREETING,
    GENERAL_PROMPT,
    NO_ANSWER_MESSAGE,
    OFF_TOPIC_MESSAGE,
    SMALLTALK_PROMPT,
    Message,
    build_context_message,
    build_messages,
    estimate_tokens,
    fit_history,
    institutional_instructions,
    with_turn_instruction,
)
from app.rag.query_router import QueryRouter, Route, RouteDecision, expand_follow_up
from app.rag.retriever import Retriever
from app.schemas.chat import ChatTurn
from app.services import prompt_service

logger = logging.getLogger("mini_rag_lab")

retriever = Retriever()
router = QueryRouter()

# Ventana que se deja libre para la respuesta del modelo al repartir el contexto.
ANSWER_RESERVE_TOKENS = 1024


def warm_up() -> None:
    """Deja listo lo que se inicializa perezosamente, antes de la primera consulta real.

    Sin esto lo paga el primer usuario: el cross-encoder tarda unos 3 s en cargar su
    modelo ONNX y el router de embeddings necesita embeber sus frases de ejemplo.
    Es best-effort: si un servicio esta caido, la app arranca igual y el fallo aparece
    cuando se use de verdad, con su mensaje propio.
    """
    try:
        retriever.qdrant_service.ensure_collection()
        vector = retriever.embedding_service.embed_query("calentamiento")
        router.classify(vector)
        if retriever.reranker is not None:
            retriever.reranker.rerank("calentamiento", ["texto de calentamiento"])
        logger.info("Calentamiento completado: reranker y router listos.")
    except Exception as exc:
        logger.warning("Calentamiento incompleto (%s); se hara en la primera consulta.", exc)


@dataclass
class RagOutcome:
    """Resultado de resolver una consulta, con el rastro de como se resolvio."""

    answer: str
    route: Route
    points: Sequence[ScoredPoint] = field(default_factory=list)
    route_scores: dict[str, float] = field(default_factory=dict)
    prompt_code: str | None = None
    generation_skipped: bool = False
    routing_ms: float | None = None
    retrieval_ms: float | None = None
    generation_ms: float | None = None
    # Que router decidio, por que, y con que pregunta se busco en los documentos.
    router: str | None = None
    route_reason: str | None = None
    search_query: str | None = None


def route_query(
    question: str, history: Sequence[ChatTurn] | None = None, mode: str | None = None
) -> RouteDecision:
    """Decide el camino con el router configurado; el de embeddings respalda al LLM."""
    if (mode or settings.ROUTER_MODE) == "llm":
        try:
            return llm_router.decide(question, history)
        except LLMError as exc:
            logger.warning("Router LLM no disponible (%s); se usa el de embeddings.", exc)

    search_query = expand_follow_up(question, history)
    vector = retriever.embedding_service.embed_query(search_query)
    route, scores = router.classify(vector)
    return RouteDecision(
        route=route, search_query=search_query, router="embedding", scores=scores, vector=vector
    )


def answer_question(
    db: Session,
    question: str,
    limit: int | None = None,
    prompt_code: str | None = None,
    history: Sequence[ChatTurn] | None = None,
) -> RagOutcome:
    """Resuelve una consulta eligiendo camino antes de gastar en recuperacion.

    Solo el camino institucional pasa por Qdrant y el reranker.

    history=None es una consulta suelta (/search): sin memoria ni saludo. Una lista,
    aunque este vacia, es una conversacion; vacia significa que empieza ahora.
    """
    top_k = limit or settings.CHAT_TOP_K

    if not settings.ROUTER_ENABLED:
        decision = RouteDecision(route=Route.INSTITUTIONAL, search_query=question, router="disabled")
        return _institutional(db, question, top_k, prompt_code, decision, None, history)

    started = time.perf_counter()
    decision = route_query(question, history)
    routing_ms = (time.perf_counter() - started) * 1000
    logger.info(
        "Router %s: '%s' -> %s (%.0f ms)", decision.router, question[:60], decision.route.value, routing_ms
    )

    if decision.route is Route.INSTITUTIONAL:
        return _institutional(db, question, top_k, prompt_code, decision, routing_ms, history)

    trace = _trace(decision, routing_ms)

    # Fuera de ambito no merece una generacion: la respuesta no depende del mensaje.
    if decision.route is Route.OFF_TOPIC:
        return RagOutcome(answer=_with_greeting(OFF_TOPIC_MESSAGE, history), **trace)

    system_prompt = SMALLTALK_PROMPT if decision.route is Route.SMALLTALK else GENERAL_PROMPT
    generation_started = time.perf_counter()
    answer = chat(_conversation(system_prompt, question, history))
    return RagOutcome(
        answer=answer,
        generation_ms=round((time.perf_counter() - generation_started) * 1000, 1),
        **trace,
    )


def _institutional(
    db: Session,
    question: str,
    top_k: int,
    prompt_code: str | None,
    decision: RouteDecision,
    routing_ms: float | None,
    history: Sequence[ChatTurn] | None,
) -> RagOutcome:
    """Camino completo: recuperar contexto y responder con el a la vista.

    Se busca con la pregunta del router (autonoma en los seguimientos), pero el modelo
    responde a la original: el historial le da el resto del contexto.
    """
    started = time.perf_counter()
    points = retriever.search(decision.search_query, top_k, vector=decision.vector)
    retrieval_ms = (time.perf_counter() - started) * 1000

    system_prompt, resolved_code = prompt_service.resolve_prompt(db, prompt_code)
    trace = _trace(decision, routing_ms)

    # Corte de calidad: sin contexto suficiente no se gasta una llamada al modelo ni se
    # le da pie a inventar sobre chunks irrelevantes.
    if not points or points[0].score < settings.CHAT_MIN_SCORE or len(points) < settings.CHAT_MIN_RESULTS:
        logger.info(
            "Contexto insuficiente para '%s' (chunks=%d, top_score=%s); no se llama al LLM.",
            decision.search_query[:60],
            len(points),
            points[0].score if points else None,
        )
        return RagOutcome(
            answer=_with_greeting(NO_ANSWER_MESSAGE, history),
            points=points,
            prompt_code=resolved_code,
            generation_skipped=True,
            retrieval_ms=round(retrieval_ms, 1),
            **trace,
        )

    chunks = [point.payload["content"] for point in points]
    generation_started = time.perf_counter()
    # Con el prompt estricto el modelo ignoraba la instruccion de saludar (0 de 10 primeros
    # turnos): aqui el saludo lo pone el codigo y al modelo se le pide no saludar.
    messages = _conversation(
        institutional_instructions(system_prompt),
        build_context_message(question, chunks),
        history,
        llm_greets=False,
    )
    answer = _with_greeting(chat(messages), history)
    generation_ms = (time.perf_counter() - generation_started) * 1000
    logger.info(
        "Respuesta del modelo '%s' con el prompt '%s' en %.2fs",
        settings.LLM_MODEL,
        resolved_code,
        generation_ms / 1000,
    )

    return RagOutcome(
        answer=answer,
        points=points,
        prompt_code=resolved_code,
        retrieval_ms=round(retrieval_ms, 1),
        generation_ms=round(generation_ms, 1),
        **trace,
    )


def _trace(decision: RouteDecision, routing_ms: float | None) -> dict:
    """Campos de RagOutcome que describen como se enruto la consulta."""
    return {
        "route": decision.route,
        "route_scores": decision.scores,
        "routing_ms": round(routing_ms, 1) if routing_ms is not None else None,
        "router": decision.router,
        "route_reason": decision.reason,
        "search_query": decision.search_query,
    }


def _conversation(
    system_prompt: str,
    user_content: str,
    history: Sequence[ChatTurn] | None,
    llm_greets: bool = True,
) -> list[Message]:
    """Mensajes para el LLM con todo el historial que quepa sin desbordar la ventana."""
    system = with_turn_instruction(system_prompt, history, llm_greets)
    room = (
        settings.LLM_NUM_CTX
        - ANSWER_RESERVE_TOKENS
        - estimate_tokens(system)
        - estimate_tokens(user_content)
    )
    turns = fit_history(
        history or [],
        min(settings.CHAT_HISTORY_MAX_TOKENS, room),
        settings.CHAT_HISTORY_ANSWER_CHARS,
    )
    return build_messages(system, user_content, turns)


def _with_greeting(message: str, history: Sequence[ChatTurn] | None) -> str:
    """Antepone el saludo fijo en el primer turno, donde el modelo no saluda por si mismo."""
    if history is not None and not history:
        return f"{FIRST_TURN_GREETING} {message}"
    return message
