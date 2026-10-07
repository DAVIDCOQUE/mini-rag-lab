import logging
import math
import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum

from app.core.config import settings
from app.rag.embedding_service import EmbeddingService
from app.schemas.chat import ChatTurn

logger = logging.getLogger("mini_rag_lab")


class Route(str, Enum):
    """Camino que sigue una consulta. Solo INSTITUTIONAL toca Qdrant."""

    INSTITUTIONAL = "institutional"
    GENERAL = "general"
    SMALLTALK = "smalltalk"
    OFF_TOPIC = "off_topic"


@dataclass
class RouteDecision:
    """Camino elegido y con que pregunta buscar si toca recuperar."""

    route: Route
    # Pregunta autonoma para Qdrant: en un seguimiento ("¿y cuanto cuesta?") ya trae
    # el tema de la conversacion. Sin reescritura es la pregunta original.
    search_query: str
    router: str  # "llm" o "embedding"
    reason: str | None = None
    scores: dict[str, float] = field(default_factory=dict)
    # Embedding de search_query si ya se calculo, para no repetirlo al buscar.
    vector: list[float] | None = None


# Frases de referencia de cada camino. La consulta se compara con las mas parecidas
# de cada grupo, no con su promedio: asi un ejemplo nuevo y distinto no diluye a los
# demas. Ampliar aqui es la forma de corregir un error de clasificacion, midiendo antes
# y despues con evaluation/evaluate_routing.py.
ROUTE_EXAMPLES: dict[Route, list[str]] = {
    Route.INSTITUTIONAL: [
        "quien es el secretario general de la universidad",
        "que dice el acuerdo del consejo directivo",
        "cual es el presupuesto de la institucion",
        "que establece la politica de bienestar institucional",
        "en que articulo se define el alcance de la politica",
        "como solicito un certificado de notas en la universidad",
        "cual es el procedimiento para la matricula academica",
        "que requisitos pide la institucion para el grado",
        "cuando se aprobo el acuerdo del consejo",
        "a quien aplica esta normativa de la universidad",
        "donde queda la biblioteca de la universidad",
        "a que hora abre la oficina de registro",
        "cuanto cuesta la matricula del semestre",
        "que becas o descuentos ofrece la universidad",
        "como saco el carne estudiantil",
        "cuando empiezan las clases y el calendario academico",
        "donde esta la oficina de bienestar universitario",
    ],
    Route.GENERAL: [
        "que es un credito academico",
        "como estudiar mejor para un examen",
        "que es una monografia",
        "como se organiza un plan de estudios",
        "que significa la nota de corte",
        "cuales son buenas tecnicas de estudio",
        "que diferencia hay entre pregrado y posgrado",
        "como cito una fuente en normas apa",
        "como escribo un ensayo academico",
    ],
    Route.SMALLTALK: [
        "hola",
        "buenos dias",
        "soy David, mucho gusto",
        "gracias por la ayuda",
        "hasta luego",
        "como estas",
        "quien eres",
        "como me llamo",
        "que te pregunte antes",
        "recuerdas lo que te dije",
        "que carrera te dije que estudio",
        "muchas gracias, eso era todo",
    ],
    Route.OFF_TOPIC: [
        "cual es la mejor receta de cocina",
        "quien gano el partido de futbol",
        "escribeme codigo en python",
        "que opinas de la politica del pais",
        "donde compro un telefono barato",
        "recomiendame una pelicula",
        "cual es la capital de un pais",
    ],
}

# Ejemplos mas parecidos que se promedian por camino: uno solo seria fragil ante un
# ejemplo atipico; todos juntos vuelve al centroide borroso.
NEAREST_EXAMPLES = 3

# Mensajes que no se entienden sin la pregunta anterior: "¿y cuanto cuesta?", "¿eso
# donde lo hago?". Se comparan sin acentos y en minusculas. Las referencias solo cuentan
# en preguntas: "gracias, eso era todo" tambien dice "eso" y es una despedida.
_STARTS_WITH_Y = re.compile(r"^\W*y\b")
_REFERENCE = re.compile(r"\b(eso|esa|ese|esos|esas|ahi|alli|tambien)\b")


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def expand_follow_up(question: str, history: Sequence[ChatTurn] | None) -> str:
    """Antepone la pregunta anterior del estudiante si el mensaje es un seguimiento.

    Sin LLM no hay reescritura: pegar el tema previo es lo que permite que el router y
    la busqueda sepan de que se habla.
    """
    text = _normalize(question)
    is_follow_up = _STARTS_WITH_Y.search(text) or ("?" in text and _REFERENCE.search(text))
    if not history or not is_follow_up:
        return question
    previous = next((turn.content for turn in reversed(history) if turn.role == "user"), None)
    return f"{previous} {question}" if previous else question


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0


def _nearest_mean(vector: list[float], group: list[list[float]]) -> float:
    similarities = sorted((_cosine(vector, example) for example in group), reverse=True)
    nearest = similarities[:NEAREST_EXAMPLES]
    return sum(nearest) / len(nearest)


class QueryRouter:
    """Decide por que camino va una consulta comparandola con centroides de ejemplos.

    Se clasifica con el mismo vector que despues usa la busqueda, de modo que en el
    camino caro el router no anade ni una llamada: el embedding habia que calcularlo
    igual. Lo que se ahorra en los demas caminos es el reranker, que es el grueso.
    """

    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()
        self._examples: dict[Route, list[list[float]]] | None = None

    def _ensure_examples(self) -> dict[Route, list[list[float]]]:
        """Vectores de los ejemplos, calculados una sola vez en una unica llamada a Ollama."""
        if self._examples is not None:
            return self._examples

        routes = list(ROUTE_EXAMPLES)
        phrases = [phrase for route in routes for phrase in ROUTE_EXAMPLES[route]]
        vectors = self.embedding_service.embed(phrases)

        examples: dict[Route, list[list[float]]] = {}
        offset = 0
        for route in routes:
            size = len(ROUTE_EXAMPLES[route])
            examples[route] = vectors[offset : offset + size]
            offset += size

        self._examples = examples
        logger.info("Ejemplos del router listos (%d caminos, %d frases)", len(examples), len(phrases))
        return examples

    def classify(self, vector: list[float]) -> tuple[Route, dict[str, float]]:
        """Camino elegido y la similitud con cada uno, para poder depurarlo."""
        examples = self._ensure_examples()
        scores = {route: _nearest_mean(vector, group) for route, group in examples.items()}

        ranked = sorted(scores, key=lambda route: scores[route], reverse=True)
        winner = ranked[0]

        # Fuera de ambito responde un texto fijo sin llamar al modelo: equivocarse ahi es
        # lo mas visible para el estudiante. Si no gana con claridad, decide el segundo.
        if winner is Route.OFF_TOPIC:
            gap = scores[winner] - scores[ranked[1]]
            if gap < settings.ROUTER_OFF_TOPIC_MARGIN:
                logger.info(
                    "Router: off_topic gana por %.4f, por debajo del margen; pasa a %s.",
                    gap,
                    ranked[1].value,
                )
                winner = ranked[1]

        # Sesgo de seguridad: equivocarse hacia el camino generativo hace que el modelo
        # responda de memoria sobre algo institucional, que es el peor fallo posible.
        # Si lo institucional queda cerca del ganador, se prefiere buscar.
        if winner is not Route.INSTITUTIONAL:
            gap = scores[winner] - scores[Route.INSTITUTIONAL]
            if gap < settings.ROUTER_SAFETY_MARGIN:
                logger.info(
                    "Router: %s gana por %.4f, por debajo del margen; se enruta a institucional.",
                    winner.value,
                    gap,
                )
                winner = Route.INSTITUTIONAL

        return winner, {route.value: round(score, 4) for route, score in scores.items()}
