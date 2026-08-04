from collections.abc import Sequence

from qdrant_client.models import ScoredPoint

from app.core.config import settings
from app.rag.embedding_service import EmbeddingService
from app.rag.qdrant_service import QdrantService
from app.rag.reranker import Reranker


class Retriever:
    """Recupera los fragmentos mas relevantes para una consulta del usuario.

    Dos etapas: bi-encoder (bge-m3) trae candidatos rapido, y opcionalmente un
    cross-encoder (reranker) los reordena por relevancia real.
    """

    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()
        self.qdrant_service = QdrantService()
        self.reranker = Reranker() if settings.RERANK_ENABLED else None

    def search(
        self, query: str, limit: int = 5, vector: list[float] | None = None
    ) -> Sequence[ScoredPoint]:
        """Embebe la consulta y devuelve los chunks mas relevantes.

        Con vector se reutiliza uno ya calculado (el router embebe la consulta antes
        de decidir el camino) y se ahorra una llamada a Ollama.
        """
        self.qdrant_service.ensure_collection()
        if vector is None:
            vector = self.embedding_service.embed_query(query)

        if self.reranker is None:
            return self.qdrant_service.search(vector, limit)

        # 1) bi-encoder: traer mas candidatos de los que se van a devolver.
        candidates = list(self.qdrant_service.search(vector, settings.RERANK_CANDIDATES))
        if not candidates:
            return candidates

        # 2) cross-encoder: reordenar por relevancia y quedarse con el top-limit.
        documents = [point.payload.get("content", "") for point in candidates]
        scores = self.reranker.rerank(query, documents)
        for point, score in zip(candidates, scores):
            point.score = float(score)
        candidates.sort(key=lambda point: point.score, reverse=True)
        return candidates[:limit]
