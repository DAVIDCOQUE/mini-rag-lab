import logging
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.documents.pdf_parser import PdfParser
from app.models.document import Document
from app.rag.chunker import Chunker
from app.rag.indexer import Indexer
from app.repositories import document_repository
from app.schemas.processing import ChunkResponse, IndexedChunks, IndexResult, ProcessingResult
from app.services import document_service

logger = logging.getLogger("mini_rag_lab")


class FileMissingError(Exception):
    """El registro existe pero el archivo fisico no esta en disco."""


class EmptyDocumentError(Exception):
    """El PDF no contiene texto extraible."""


class IndexingError(Exception):
    """Fallo la generacion de embeddings o el guardado en Qdrant."""


class DocumentProcessingService:
    """Procesa un documento: abrir PDF -> extraer texto -> dividir en chunks (-> indexar)."""

    def __init__(self) -> None:
        self.parser = PdfParser()
        self.chunker = Chunker()
        self.indexer = Indexer()

    def _extract_and_chunk(self, document: Document):
        """Verifica el archivo, extrae el texto por pagina y lo trocea. Devuelve (pages, chunks)."""
        file_path = Path(document.storage_path)
        if not file_path.exists():
            raise FileMissingError

        # Un PDF corrupto o sin texto se trata igual: sin contenido.
        try:
            pages = self.parser.extract_pages(file_path)
        except Exception as exc:
            logger.warning("No se pudo leer el PDF %s: %s", file_path, exc)
            raise EmptyDocumentError("No fue posible extraer contenido del PDF.") from exc
        if not any(page.strip() for page in pages):
            raise EmptyDocumentError("No fue posible extraer contenido del PDF.")

        chunks = self.chunker.split_pages(pages)
        return pages, chunks

    def process_document(self, db: Session, document_id: uuid.UUID) -> ProcessingResult:
        """Vista previa del procesamiento: extrae y trocea, sin persistir nada."""
        document = document_service.get_document(db, document_id)
        pages, chunks = self._extract_and_chunk(document)

        chunk_items = [
            ChunkResponse(
                index=i,
                page=chunk.metadata["page"],
                characters=len(chunk.page_content),
                content=chunk.page_content,
            )
            for i, chunk in enumerate(chunks)
        ]
        total_characters = sum(len(page) for page in pages)
        logger.info(
            "Documento procesado %s: %d paginas, %d caracteres, %d chunks",
            document_id,
            len(pages),
            total_characters,
            len(chunk_items),
        )
        return ProcessingResult(
            document_id=document.id,
            total_pages=len(pages),
            total_characters=total_characters,
            total_chunks=len(chunk_items),
            chunks=chunk_items,
        )

    def index_document(self, db: Session, document_id: uuid.UUID) -> IndexResult:
        """Pipeline completo: extraer -> trocear -> embeddings -> Qdrant, actualizando status."""
        document = document_service.get_document(db, document_id)

        # Errores de contenido se resuelven antes de marcar PROCESSING.
        _, chunks = self._extract_and_chunk(document)

        self._set_status(db, document, "PROCESSING")
        try:
            total_chunks = self.indexer.index_chunks(document.id, chunks)
        except Exception as exc:
            self._set_status(db, document, "ERROR")
            logger.warning("Fallo el indexado de %s: %s", document_id, exc)
            raise IndexingError("No fue posible indexar el documento.") from exc

        self._set_status(db, document, "INDEXED")
        logger.info("Documento indexado %s: %d chunks en Qdrant", document_id, total_chunks)
        return IndexResult(document_id=document.id, total_chunks=total_chunks, status="INDEXED")

    def get_indexed_chunks(self, db: Session, document_id: uuid.UUID) -> IndexedChunks:
        """Lee de Qdrant los chunks guardados de un documento (ordenados por chunk_index)."""
        document = document_service.get_document(db, document_id)
        records = self.indexer.qdrant_service.list_by_document(document.id)
        chunks = sorted(
            (
                ChunkResponse(
                    index=record.payload["chunk_index"],
                    page=record.payload["page"],
                    characters=len(record.payload["content"]),
                    content=record.payload["content"],
                )
                for record in records
            ),
            key=lambda chunk: chunk.index,
        )
        return IndexedChunks(
            document_id=document.id, total_chunks=len(chunks), chunks=chunks
        )

    def _set_status(self, db: Session, document: Document, status: str) -> None:
        document.status = status
        document_repository.update(db, document)
