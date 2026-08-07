import logging
import unicodedata
from pathlib import Path

import fitz  # PyMuPDF
import numpy as np

from app.documents.ocr import OCR

logger = logging.getLogger("mini_rag_lab")

# Resolucion del render para OCR: 2x (144 dpi) da mejor deteccion que el render
# por defecto (72 dpi) sin disparar el tiempo de procesamiento.
OCR_RENDER_MATRIX = fitz.Matrix(2, 2)


class PdfParser:
    """Extrae el texto de un PDF usando PyMuPDF, conservando la separacion por pagina.

    PyMuPDF da mejor calidad de extraccion que pypdf (menos espacios espurios y acentos
    partidos). Se normaliza a Unicode NFC para recomponer acentos descompuestos.

    Si una pagina no trae texto (tipicamente un PDF escaneado), se renderiza esa
    pagina a imagen y se pasa por OCR (EasyOCR, en ocr.py) en vez de dejarla vacia.
    """

    def __init__(self, ocr: OCR | None = None) -> None:
        # OCR es inyectable para pruebas; por defecto se crea uno propio (carga perezosa).
        self.ocr = ocr or OCR()

    def extract_pages(self, file_path: Path) -> list[str]:
        """Devuelve el texto de cada pagina (indice 0 = pagina 1), normalizado a NFC."""
        with fitz.open(str(file_path)) as document:
            pages: list[str] = []
            for page in document:
                text = page.get_text()
                if not text.strip():
                    # Pagina sin texto extraible (probable escaneo) -> intentar OCR.
                    text = self._ocr_page(page)
                pages.append(unicodedata.normalize("NFC", text))
            return pages

    def _ocr_page(self, page: "fitz.Page") -> str:
        """Renderiza una pagina a imagen y le aplica OCR. Nunca detiene la extraccion:
        si algo falla, se registra el error y la pagina queda como texto vacio."""
        try:
            pixmap = page.get_pixmap(matrix=OCR_RENDER_MATRIX)
            image = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(
                pixmap.height, pixmap.width, pixmap.n
            )
            return self.ocr.image_to_text(image)
        except Exception as exc:
            logger.warning("OCR fallo en la pagina %d: %s", page.number + 1, exc)
            return ""
