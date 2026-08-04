import uuid

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str
    limit: int = 5
    # Pasar los chunks recuperados por el LLM, igual que hace /chat. Por defecto
    # apagado: la busqueda pura sirve para medir recuperacion sin coste de modelo.
    generate: bool = False
    # Variante de prompt a usar en esta consulta. Sin code manda la variante activa
    # y, si no hay ninguna, el prompt del repositorio.
    prompt_code: str | None = None


class SearchResultItem(BaseModel):
    document_id: uuid.UUID
    page: int
    chunk_index: int
    content: str
    score: float


class SearchTimings(BaseModel):
    """Coste de cada etapa del flujo, en milisegundos. Nulo lo que no llego a ocurrir."""

    # Incluye el embedding de la consulta, que el camino institucional reutiliza.
    routing_ms: float | None = None
    retrieval_ms: float | None = None
    generation_ms: float | None = None
    total_ms: float


class SearchResponse(BaseModel):
    query: str
    total: int
    results: list[SearchResultItem]
    timings: SearchTimings
    answer: str | None = None
    # El contexto no alcanzo el umbral de relevancia: se devuelve el fallback sin
    # gastar una llamada al modelo.
    generation_skipped: bool = False
    # Prompt con el que se genero la respuesta, para que la vista pueda decir de que
    # instrucciones salio lo que se esta leyendo.
    prompt_code: str | None = None
    # Camino elegido por el router y su similitud con cada uno, para poder ver por que.
    route: str | None = None
    route_scores: dict[str, float] = Field(default_factory=dict)
