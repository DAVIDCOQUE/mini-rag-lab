from collections.abc import Sequence

from app.core.config import settings
from app.rag import llm_service
from app.rag.llm_service import LLMError
from app.rag.prompt_builder import fit_history
from app.rag.query_router import Route, RouteDecision
from app.schemas.chat import ChatTurn

# Validado con evaluation/evaluate_routing.py. Con llama3.1:8b dos detalles cambiaron el
# resultado: pedir "reason" antes que "route" y separar el mensaje del historial; sin
# eso, un mensaje suelto etiquetado como conversacion acababa siempre en "conversation".
ROUTER_SYSTEM_PROMPT = """Eres el enrutador del asistente de un quiosco universitario. \
Clasificas el MENSAJE A CLASIFICAR del estudiante en una ruta:
- institutional: pide un dato propio de la universidad (normas, acuerdos, politicas, tramites, \
requisitos, personas, cargos, lugares, horarios, costos). Tambien las reglas academicas: notas, \
asistencia, perder, cancelar o habilitar materias, matricula y grado; aunque suenen generales, \
cada universidad las fija en su reglamento. Y los seguimientos de un tema institucional \
("¿y cuanto cuesta?").
- general: tema academico general que no depende de esta universidad.
- conversation: SOLO saludos, despedidas, agradecimientos o preguntas sobre la propia charla \
(su nombre, que dijo antes).
- off_topic: nada que ver con lo academico ni con la universidad (cocina, deportes, compras, \
entretenimiento, politica nacional, cultura general, pedir que escribas codigo o tareas).
El historial solo sirve para entender referencias; clasifica unicamente el mensaje.
Primero escribe "reason" (una frase), luego "route", y si es institutional escribe en "query" una \
pregunta autonoma resolviendo "eso", "y...", etc.

Ejemplos:
"¿Quien es el rector?" -> institutional
"¿Que dice el reglamento estudiantil?" -> institutional
"(tras hablar de matricula) ¿y cuando cierra?" -> institutional, query: "¿Cuando cierra la matricula?"
"¿Que es una tesis?" -> general
"Hola" -> conversation
"¿Como me llamo?" -> conversation
"Recomiendame una serie" -> off_topic"""

# "conversation" se le describe mejor al modelo que "smalltalk": una pregunta sobre lo
# dicho antes no es charla trivial, y con ese nombre la clasificaba mal.
_LABELS: dict[str, Route] = {
    "institutional": Route.INSTITUTIONAL,
    "general": Route.GENERAL,
    "conversation": Route.SMALLTALK,
    "off_topic": Route.OFF_TOPIC,
}

ROUTER_SCHEMA = {
    "type": "object",
    "properties": {
        "reason": {"type": "string"},
        "route": {"type": "string", "enum": list(_LABELS)},
        "query": {"type": "string"},
    },
    "required": ["reason", "route", "query"],
}

# Para decidir basta el hilo reciente; el historial completo encareceria cada mensaje.
HISTORY_MAX_TOKENS = 1500
HISTORY_ANSWER_CHARS = 300


def decide(question: str, history: Sequence[ChatTurn] | None) -> RouteDecision:
    """Camino y pregunta de busqueda decididos por el LLM. LLMError si no se puede confiar en la salida."""
    turns = fit_history(history or [], HISTORY_MAX_TOKENS, HISTORY_ANSWER_CHARS)
    history_text = "\n".join(f"{turn['role']}: {turn['content']}" for turn in turns) or "(sin historial)"
    messages = [
        {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
        {"role": "user", "content": f"Historial:\n{history_text}\n\nMENSAJE A CLASIFICAR: {question}"},
    ]

    data = llm_service.chat_structured(messages, ROUTER_SCHEMA, timeout=settings.ROUTER_LLM_TIMEOUT_S)

    route = _LABELS.get(str(data.get("route")))
    if route is None:
        raise LLMError(f"Ruta desconocida del router: {data.get('route')!r}")

    query = str(data.get("query") or "").strip()
    return RouteDecision(
        route=route,
        search_query=query if route is Route.INSTITUTIONAL and query else question,
        router="llm",
        reason=str(data.get("reason") or "").strip() or None,
    )
