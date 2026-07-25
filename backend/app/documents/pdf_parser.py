import unicodedata
from pathlib import Path

import fitz  # PyMuPDF


class PdfParser:
    """Extrae el texto de un PDF usando PyMuPDF, conservando la separacion por pagina.

    PyMuPDF da mejor calidad de extraccion que pypdf (menos espacios espurios y acentos
    partidos). Se normaliza a Unicode NFC para recomponer acentos descompuestos.
    """

    def extract_pages(self, file_path: Path) -> list[str]:
        """Devuelve el texto de cada pagina (indice 0 = pagina 1), normalizado a NFC."""
        with fitz.open(str(file_path)) as document:
            return [unicodedata.normalize("NFC", page.get_text()) for page in document]
