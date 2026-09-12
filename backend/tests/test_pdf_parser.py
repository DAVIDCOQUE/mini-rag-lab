import fitz
import pytest

from app.documents.pdf_parser import PdfParser

TEXTO_DE_PRUEBA = "ACUERDO No. 012 de 2024"


class OcrFalso:
    """Doble del OCR: cuenta las llamadas y devuelve un texto fijo o lanza un error."""

    def __init__(self, texto: str = "texto reconocido", error: Exception | None = None) -> None:
        self.texto = texto
        self.error = error
        self.llamadas = 0

    def image_to_text(self, image) -> str:
        self.llamadas += 1
        if self.error is not None:
            raise self.error
        return self.texto


def _pdf_con_capa_de_texto(destino, paginas: int = 1):
    documento = fitz.open()
    for numero in range(paginas):
        pagina = documento.new_page()
        pagina.insert_text((72, 100), f"{TEXTO_DE_PRUEBA} pagina {numero + 1}", fontsize=14)
    documento.save(destino)
    return destino


def _pdf_escaneado(destino):
    """PDF cuyo contenido es solo imagen, como un escaneo: get_text() devuelve vacio."""
    origen = fitz.open()
    pagina = origen.new_page()
    pagina.insert_text((72, 100), TEXTO_DE_PRUEBA, fontsize=14)

    escaneado = fitz.open()
    for pagina_origen in origen:
        pixmap = pagina_origen.get_pixmap(dpi=72)
        nueva = escaneado.new_page(width=pagina_origen.rect.width, height=pagina_origen.rect.height)
        nueva.insert_image(nueva.rect, pixmap=pixmap)
    escaneado.save(destino)
    return destino


@pytest.fixture
def pdf_escaneado(tmp_path):
    return _pdf_escaneado(tmp_path / "escaneado.pdf")


def test_una_pagina_con_texto_no_pasa_por_el_ocr(tmp_path):
    ocr = OcrFalso()
    ruta = _pdf_con_capa_de_texto(tmp_path / "con_texto.pdf")

    paginas = PdfParser(ocr=ocr).extract_pages(ruta)

    assert TEXTO_DE_PRUEBA in paginas[0]
    assert ocr.llamadas == 0  # el OCR es caro: solo se usa cuando no hay texto


def test_una_pagina_sin_texto_cae_en_el_ocr(pdf_escaneado):
    ocr = OcrFalso(texto="lo que leyo el ocr")

    paginas = PdfParser(ocr=ocr).extract_pages(pdf_escaneado)

    assert ocr.llamadas == 1
    assert paginas[0] == "lo que leyo el ocr"


def test_sin_la_dependencia_del_ocr_la_extraccion_no_se_rompe(pdf_escaneado):
    # Regresion: easyocr ausente dejaba la pagina vacia, pero no debe tumbar el proceso.
    ocr = OcrFalso(error=ImportError("No module named 'easyocr'"))

    paginas = PdfParser(ocr=ocr).extract_pages(pdf_escaneado)

    assert paginas == [""]


def test_un_fallo_del_ocr_no_detiene_las_demas_paginas(tmp_path):
    # Regresion: la barra de progreso de easyocr lanzaba UnicodeEncodeError en consolas
    # cp1252 y ese error no debe propagarse fuera de la pagina que lo provoca.
    ocr = OcrFalso(error=UnicodeEncodeError("charmap", "█", 0, 1, "undefined"))
    ruta = _pdf_con_capa_de_texto(tmp_path / "mixto.pdf", paginas=2)

    paginas = PdfParser(ocr=ocr).extract_pages(ruta)

    assert len(paginas) == 2
    assert all(TEXTO_DE_PRUEBA in pagina for pagina in paginas)


def test_el_texto_se_normaliza_a_nfc(tmp_path):
    documento = fitz.open()
    documento.new_page().insert_text((72, 100), "Bogota", fontsize=14)
    ruta = tmp_path / "acentos.pdf"
    documento.save(ruta)

    paginas = PdfParser(ocr=OcrFalso()).extract_pages(ruta)

    import unicodedata

    assert paginas[0] == unicodedata.normalize("NFC", paginas[0])
