import uuid

from langchain_core.documents import Document

from app.rag.embedding_service import EmbeddingService
from app.rag.qdrant_service import QdrantService


class Indexer:
    """Orquesta el indexado: chunks -> embeddings -> almacenamiento en Qdrant."""

    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()
        self.qdrant_service = QdrantService()

    def index_chunks(self, document_id: uuid.UUID, chunks: list[Document]) -> int:
        """Genera embeddings de los chunks y los guarda en Qdrant. Devuelve cuantos indexo."""
        self.qdrant_service.ensure_collection()
        # Reindexar es idempotente: se borran los vectores previos del documento.
        self.qdrant_service.delete_by_document(document_id)

        vectors = self.embedding_service.embed([chunk.page_content for chunk in chunks])
        items = [
            {
                "id": str(uuid.uuid4()),
                "vector": vector,
                "payload": {
                    "document_id": str(document_id),
                    "page": chunk.metadata["page"],
                    "chunk_index": i,
                    "content": chunk.page_content,
                },
            }
            for i, (chunk, vector) in enumerate(zip(chunks, vectors))
        ]
        self.qdrant_service.upsert_chunks(items)
        return len(items)
