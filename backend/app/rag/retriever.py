from collections.abc import Sequence

from qdrant_client.models import ScoredPoint

from app.rag.embedding_service import EmbeddingService
from app.rag.qdrant_service import QdrantService


class Retriever:
    """Recupera los fragmentos mas relevantes para una consulta del usuario."""

    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()
        self.qdrant_service = QdrantService()

    def search(self, query: str, limit: int = 5) -> Sequence[ScoredPoint]:
        """Embebe la consulta y devuelve los chunks mas cercanos en Qdrant."""
        self.qdrant_service.ensure_collection()
        vector = self.embedding_service.embed_query(query)
        return self.qdrant_service.search(vector, limit)
