import logging
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.documents.pdf_parser import PdfParser
from app.rag.chunker import Chunker
from app.schemas.processing import ChunkResponse, ProcessingResult
from app.services import document_service

logger = logging.getLogger("mini_rag_lab")


class FileMissingError(Exception):
    """El registro existe pero el archivo fisico no esta en disco."""


class EmptyDocumentError(Exception):
    """El PDF no contiene texto extraible."""


class DocumentProcessingService:
    """Procesa un documento: abrir PDF -> extraer texto -> dividir en chunks."""

    def __init__(self) -> None:
        self.parser = PdfParser()
        self.chunker = Chunker()

    def process_document(self, db: Session, document_id: uuid.UUID) -> ProcessingResult:
        # 1. Buscar el documento (lanza DocumentNotFoundError si no existe).
        document = document_service.get_document(db, document_id)

        # 2. Verificar que el archivo fisico exista.
        file_path = Path(document.storage_path)
        if not file_path.exists():
            raise FileMissingError

        # 3. Extraer el texto por pagina (un PDF corrupto o sin texto se trata igual: sin contenido).
        try:
            pages = self.parser.extract_pages(file_path)
        except Exception as exc:
            logger.warning("No se pudo leer el PDF %s: %s", file_path, exc)
            raise EmptyDocumentError("No fue posible extraer contenido del PDF.") from exc
        if not any(page.strip() for page in pages):
            raise EmptyDocumentError("No fue posible extraer contenido del PDF.")

        # 4. Dividir en chunks conservando la pagina de origen.
        chunks = self.chunker.split_pages(pages)

        # --- Punto de extension (siguiente fase) ---
        # Aqui se generaran los embeddings de `chunks` y se guardaran en Qdrant
        # (cada chunk ya trae su pagina en metadata), sin cambiar este flujo.

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
