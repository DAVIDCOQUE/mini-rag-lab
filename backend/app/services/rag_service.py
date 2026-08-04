import logging
import time
from collections.abc import Sequence
from dataclasses import dataclass, field

from qdrant_client.models import ScoredPoint
from sqlalchemy.orm import Session

from app.core.config import settings
from app.rag.llm_service import generate
from app.rag.prompt_builder import (
    GENERAL_PROMPT,
    NO_ANSWER_MESSAGE,
    OFF_TOPIC_MESSAGE,
    SMALLTALK_PROMPT,
    build_prompt,
    build_simple_prompt,
)
from app.rag.query_router import QueryRouter, Route
from app.rag.retriever import Retriever
from app.services import prompt_service

logger = logging.getLogger("mini_rag_lab")

retriever = Retriever()
router = QueryRouter()


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


def answer_question(
    db: Session, question: str, limit: int | None = None, prompt_code: str | None = None
) -> RagOutcome:
    """Resuelve una consulta eligiendo camino antes de gastar en recuperacion.

    Solo el camino institucional pasa por Qdrant y el reranker. El router clasifica con
    el mismo vector que luego usa la busqueda, asi que en ese camino no cuesta nada.
    """
    top_k = limit or settings.CHAT_TOP_K

    if not settings.ROUTER_ENABLED:
        return _institutional(db, question, top_k, prompt_code, Route.INSTITUTIONAL, {}, None)

    started = time.perf_counter()
    vector = retriever.embedding_service.embed_query(question)
    route, scores = router.classify(vector)
    routing_ms = (time.perf_counter() - started) * 1000
    logger.info("Router: '%s' -> %s (%.0f ms)", question[:60], route.value, routing_ms)

    if route is Route.INSTITUTIONAL:
        return _institutional(db, question, top_k, prompt_code, route, scores, routing_ms, vector)

    # Fuera de ambito no merece una generacion: la respuesta no depende del mensaje.
    if route is Route.OFF_TOPIC:
        return RagOutcome(
            answer=OFF_TOPIC_MESSAGE,
            route=route,
            route_scores=scores,
            routing_ms=round(routing_ms, 1),
        )

    system_prompt = SMALLTALK_PROMPT if route is Route.SMALLTALK else GENERAL_PROMPT
    generation_started = time.perf_counter()
    answer = generate(build_simple_prompt(question, system_prompt))
    return RagOutcome(
        answer=answer,
        route=route,
        route_scores=scores,
        routing_ms=round(routing_ms, 1),
        generation_ms=round((time.perf_counter() - generation_started) * 1000, 1),
    )


def _institutional(
    db: Session,
    question: str,
    top_k: int,
    prompt_code: str | None,
    route: Route,
    scores: dict[str, float],
    routing_ms: float | None,
    vector: list[float] | None = None,
) -> RagOutcome:
    """Camino completo: recuperar contexto y responder con el a la vista."""
    started = time.perf_counter()
    points = retriever.search(question, top_k, vector=vector)
    retrieval_ms = (time.perf_counter() - started) * 1000

    system_prompt, resolved_code = prompt_service.resolve_prompt(db, prompt_code)

    # Corte de calidad: sin contexto suficiente no se gasta una llamada al modelo ni se
    # le da pie a inventar sobre chunks irrelevantes.
    if not points or points[0].score < settings.CHAT_MIN_SCORE or len(points) < settings.CHAT_MIN_RESULTS:
        logger.info(
            "Contexto insuficiente para '%s' (chunks=%d, top_score=%s); no se llama al LLM.",
            question[:60],
            len(points),
            points[0].score if points else None,
        )
        return RagOutcome(
            answer=NO_ANSWER_MESSAGE,
            route=route,
            points=points,
            route_scores=scores,
            prompt_code=resolved_code,
            generation_skipped=True,
            routing_ms=round(routing_ms, 1) if routing_ms is not None else None,
            retrieval_ms=round(retrieval_ms, 1),
        )

    chunks = [point.payload["content"] for point in points]
    generation_started = time.perf_counter()
    answer = generate(build_prompt(question, chunks, system_prompt))
    generation_ms = (time.perf_counter() - generation_started) * 1000
    logger.info(
        "Respuesta del modelo '%s' con el prompt '%s' en %.2fs",
        settings.LLM_MODEL,
        resolved_code,
        generation_ms / 1000,
    )

    return RagOutcome(
        answer=answer,
        route=route,
        points=points,
        route_scores=scores,
        prompt_code=resolved_code,
        routing_ms=round(routing_ms, 1) if routing_ms is not None else None,
        retrieval_ms=round(retrieval_ms, 1),
        generation_ms=round(generation_ms, 1),
    )
