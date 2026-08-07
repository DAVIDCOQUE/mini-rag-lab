import logging

import numpy as np

logger = logging.getLogger("mini_rag_lab")

# Idiomas soportados por el reader. 'es' cubre el material institucional; 'en' es
# habitual en anexos/citas. Ampliar esta lista si aparecen documentos en otro idioma.
OCR_LANGUAGES = ["es", "en"]


class OCR:
    """Extrae texto de una imagen mediante EasyOCR.

    Unica responsabilidad: recibir una imagen ya renderizada y devolver el texto
    detectado. No sabe nada de PDFs ni de paginas; eso lo decide PdfParser.
    """

    def __init__(self) -> None:
        # El Reader carga los modelos a memoria; se crea una sola vez y se reutiliza
        # en todas las paginas/documentos que necesiten OCR (gpu=False: laboratorio sin GPU).
        self._reader = None

    def _get_reader(self):
        if self._reader is None:
            import easyocr  # import perezoso: evita cargar el modelo si nunca se usa OCR

            self._reader = easyocr.Reader(OCR_LANGUAGES, gpu=False)
        return self._reader

    def image_to_text(self, image: np.ndarray) -> str:
        """Recibe una imagen (array HxWxC) y devuelve el texto detectado, unido por saltos de linea."""
        reader = self._get_reader()
        # detail=0 -> devuelve solo las cadenas de texto, sin cajas ni score
        lines = reader.readtext(image, detail=0, paragraph=True)
        return "\n".join(lines)
