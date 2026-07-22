from pathlib import Path

from pypdf import PdfReader


class PdfParser:
    """Extrae el texto de un PDF usando pypdf, conservando la separacion por pagina."""

    def extract_pages(self, file_path: Path) -> list[str]:
        """Devuelve el texto de cada pagina (indice 0 = pagina 1)."""
        reader = PdfReader(str(file_path))
        return [(page.extract_text() or "") for page in reader.pages]
