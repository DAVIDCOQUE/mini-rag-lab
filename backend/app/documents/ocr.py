import contextlib
import io
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

    # El Reader ocupa ~100 MB en memoria. Se comparte entre instancias para no
    # duplicarlo si llega a crearse mas de un parser (gpu=False: laboratorio sin GPU).
    _reader = None

    def _get_reader(self):
        if OCR._reader is None:
            import easyocr  # import perezoso: evita cargar el modelo si nunca se usa OCR

            # EasyOCR dibuja una barra de progreso con caracteres de bloque al descargar
            # sus modelos. En una consola cp1252 (Windows) eso lanza UnicodeEncodeError y
            # tumba la primera extraccion, asi que su salida se descarta.
            with contextlib.redirect_stdout(io.StringIO()):
                OCR._reader = easyocr.Reader(OCR_LANGUAGES, gpu=False)
        return OCR._reader

    def warm_up(self) -> None:
        """Descarga y carga los modelos sin procesar ninguna imagen."""
        self._get_reader()

    def image_to_text(self, image: np.ndarray) -> str:
        """Recibe una imagen (array HxWxC) y devuelve el texto detectado, unido por saltos de linea."""
        reader = self._get_reader()
        # detail=0 -> devuelve solo las cadenas de texto, sin cajas ni score
        lines = reader.readtext(image, detail=0, paragraph=True)
        return "\n".join(lines)


def warm_up() -> None:
    """Deja el OCR listo al arrancar, no en el primer documento escaneado.

    Los modelos son ~100 MB que se descargan la primera vez: pagarlo aqui evita que
    el primer PDF sin capa de texto se procese vacio mientras se descargan. Es
    best-effort, igual que el calentamiento del RAG: si falla, la app arranca y el
    problema reaparece al usar OCR, ya con su mensaje propio.
    """
    try:
        OCR().warm_up()
        logger.info("OCR listo: modelos cargados.")
    except Exception as exc:
        logger.error("OCR no disponible (%s); los PDF escaneados quedaran sin texto.", exc)
