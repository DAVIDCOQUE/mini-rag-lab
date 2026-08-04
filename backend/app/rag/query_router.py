import logging
import math
from enum import Enum

from app.core.config import settings
from app.rag.embedding_service import EmbeddingService

logger = logging.getLogger("mini_rag_lab")


class Route(str, Enum):
    """Camino que sigue una consulta. Solo INSTITUTIONAL toca Qdrant."""

    INSTITUTIONAL = "institutional"
    GENERAL = "general"
    SMALLTALK = "smalltalk"
    OFF_TOPIC = "off_topic"


# Frases de referencia de cada camino. El router compara la consulta contra el
# centroide de cada grupo, asi que importan mas la variedad y el vocabulario tipico
# que la cantidad. Ampliar aqui es la forma de corregir un error de clasificacion.
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
    ],
    Route.GENERAL: [
        "que es un credito academico",
        "como estudiar mejor para un examen",
        "que es una monografia",
        "como se organiza un plan de estudios",
        "que significa la nota de corte",
        "cuales son buenas tecnicas de estudio",
        "que diferencia hay entre pregrado y posgrado",
    ],
    Route.SMALLTALK: [
        "hola",
        "buenos dias",
        "soy David, mucho gusto",
        "gracias por la ayuda",
        "hasta luego",
        "como estas",
    ],
    Route.OFF_TOPIC: [
        "cual es la mejor receta de cocina",
        "quien gano el partido de futbol",
        "escribeme codigo en python",
        "que opinas de la politica del pais",
        "donde compro un telefono barato",
        "recomiendame una pelicula",
    ],
}


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0


class QueryRouter:
    """Decide por que camino va una consulta comparandola con centroides de ejemplos.

    Se clasifica con el mismo vector que despues usa la busqueda, de modo que en el
    camino caro el router no anade ni una llamada: el embedding habia que calcularlo
    igual. Lo que se ahorra en los demas caminos es el reranker, que es el grueso.
    """

    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()
        self._centroids: dict[Route, list[float]] | None = None

    def _ensure_centroids(self) -> dict[Route, list[float]]:
        """Centroides calculados una sola vez, en una unica llamada a Ollama."""
        if self._centroids is not None:
            return self._centroids

        routes = list(ROUTE_EXAMPLES)
        phrases = [phrase for route in routes for phrase in ROUTE_EXAMPLES[route]]
        vectors = self.embedding_service.embed(phrases)

        centroids: dict[Route, list[float]] = {}
        offset = 0
        for route in routes:
            size = len(ROUTE_EXAMPLES[route])
            group = vectors[offset : offset + size]
            centroids[route] = [sum(values) / len(values) for values in zip(*group)]
            offset += size

        self._centroids = centroids
        logger.info("Centroides del router listos (%d caminos)", len(centroids))
        return centroids

    def classify(self, vector: list[float]) -> tuple[Route, dict[str, float]]:
        """Camino elegido y la similitud con cada centroide, para poder depurarlo."""
        centroids = self._ensure_centroids()
        scores = {route: _cosine(vector, centroid) for route, centroid in centroids.items()}

        winner = max(scores, key=lambda route: scores[route])

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
