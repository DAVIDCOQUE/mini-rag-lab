import re
from collections import Counter

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings

# Orden de corte: parrafo -> frase -> clausula -> palabra -> caracter.
# Al preferir '. ', '? ', '! ' los chunks terminan en frases completas.
SEPARATORS = ["\n\n", ". ", "? ", "! ", "; ", ", ", " ", ""]


class Chunker:
    """Divide el texto en chunks respetando frases (RecursiveCharacterTextSplitter)."""

    def __init__(self, chunk_size: int | None = None, chunk_overlap: int | None = None) -> None:
        # Los tamanos salen de la config; los parametros permiten sobreescribirlos en pruebas.
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size or settings.CHUNK_SIZE,
            chunk_overlap=chunk_overlap or settings.CHUNK_OVERLAP,
            separators=SEPARATORS,
            keep_separator="end",
        )

    def split(self, text: str) -> list[str]:
        return self.splitter.split_text(self._reflow(text))

    def split_pages(self, pages: list[str]) -> list[Document]:
        """Trocea cada pagina por separado y conserva su numero en metadata['page'] (1-indexado)."""
        cleaned = self._strip_repeated_lines(pages)
        texts: list[str] = []
        metadatas: list[dict] = []
        for page_number, page_text in enumerate(cleaned, start=1):
            reflowed = self._reflow(page_text)
            if reflowed:
                texts.append(reflowed)
                metadatas.append({"page": page_number})
        return self.splitter.create_documents(texts, metadatas=metadatas)

    @staticmethod
    def _strip_repeated_lines(pages: list[str]) -> list[str]:
        """Quita headers/footers: lineas repetidas en la mayoria de paginas, conservando la 1a aparicion."""
        if len(pages) < 2:
            return pages
        counts: Counter[str] = Counter()
        for page in pages:
            unique = {line.strip() for line in page.splitlines() if line.strip()}
            counts.update(unique)
        threshold = max(2, round(len(pages) * 0.5))
        boilerplate = {line for line, count in counts.items() if count >= threshold}

        seen: set[str] = set()
        result: list[str] = []
        for page in pages:
            kept: list[str] = []
            for line in page.splitlines():
                key = line.strip()
                if key in boilerplate:
                    if key in seen:  # duplicado -> se descarta
                        continue
                    seen.add(key)  # primera aparicion -> se conserva
                kept.append(line)
            result.append("\n".join(kept))
        return result

    @staticmethod
    def _reflow(text: str) -> str:
        """Une los saltos de linea de line-wrap (conservando parrafos) para no cortar frases."""
        text = re.sub(r"[ \t]+", " ", text)  # espacios/tabs -> un espacio
        text = re.sub(r" *\n *", "\n", text)  # limpiar espacios alrededor de saltos
        text = re.sub(r"\n{2,}", "\n\n", text)  # 2+ saltos -> parrafo
        text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)  # salto simple (line-wrap) -> espacio
        text = re.sub(r" {2,}", " ", text)
        return text.strip()
