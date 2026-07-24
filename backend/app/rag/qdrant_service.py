import uuid
from collections.abc import Sequence

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    ScoredPoint,
    VectorParams,
)

from app.core.config import settings


class QdrantService:
    """Gestiona la conexion y las operaciones contra la base vectorial Qdrant."""

    def __init__(self) -> None:
        self.client = QdrantClient(
            host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, timeout=30
        )
        self.collection = settings.QDRANT_COLLECTION

    def ensure_collection(self) -> None:
        """Crea la coleccion si no existe (vectores de EMBEDDING_DIM, distancia coseno)."""
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                self.collection,
                vectors_config=VectorParams(
                    size=settings.EMBEDDING_DIM, distance=Distance.COSINE
                ),
            )

    def upsert_chunks(self, items: list[dict]) -> None:
        """Inserta/actualiza puntos. Cada item: {id, vector, payload}."""
        points = [
            PointStruct(id=item["id"], vector=item["vector"], payload=item["payload"])
            for item in items
        ]
        self.client.upsert(self.collection, points=points)

    def delete_by_document(self, document_id: uuid.UUID) -> None:
        """Elimina todos los vectores asociados a un documento."""
        self.client.delete(
            self.collection,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id", match=MatchValue(value=str(document_id))
                    )
                ]
            ),
        )

    def search(self, vector: list[float], limit: int) -> Sequence[ScoredPoint]:
        """Devuelve los puntos mas cercanos al vector de consulta."""
        response = self.client.query_points(
            self.collection, query=vector, limit=limit, with_payload=True
        )
        return response.points

    def list_by_document(self, document_id: uuid.UUID, limit: int = 1000) -> list:
        """Devuelve todos los puntos guardados de un documento (sin el vector)."""
        self.ensure_collection()
        records, _ = self.client.scroll(
            self.collection,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="document_id", match=MatchValue(value=str(document_id))
                    )
                ]
            ),
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )
        return records
