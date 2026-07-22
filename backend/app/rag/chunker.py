from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings


class Chunker:
    """Divide el texto de los documentos en fragmentos (chunks) con RecursiveCharacterTextSplitter."""

    def __init__(self, chunk_size: int | None = None, chunk_overlap: int | None = None) -> None:
        # Los tamanos salen de la config; los parametros permiten sobreescribirlos en pruebas.
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size or settings.CHUNK_SIZE,
            chunk_overlap=chunk_overlap or settings.CHUNK_OVERLAP,
        )

    def split(self, text: str) -> list[str]:
        return self.splitter.split_text(text)

    def split_pages(self, pages: list[str]) -> list[Document]:
        """Trocea cada pagina por separado y conserva su numero en metadata['page'] (1-indexado)."""
        texts: list[str] = []
        metadatas: list[dict] = []
        for page_number, page_text in enumerate(pages, start=1):
            if page_text.strip():
                texts.append(page_text)
                metadatas.append({"page": page_number})
        return self.splitter.create_documents(texts, metadatas=metadatas)
