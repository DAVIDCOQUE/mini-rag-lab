from app.rag.chunker import Chunker


def test_reflow_une_el_line_wrap_pero_conserva_parrafos():
    texto = "Una frase partida\npor el ancho de la linea.\n\nOtro parrafo."

    assert Chunker._reflow(texto) == "Una frase partida por el ancho de la linea.\n\nOtro parrafo."


def test_reflow_colapsa_espacios_repetidos():
    assert Chunker._reflow("hola   mundo\t\tde  nuevo") == "hola mundo de nuevo"


def test_strip_repeated_lines_quita_el_encabezado_menos_la_primera_vez():
    paginas = [
        "ACUERDO No. 008\nContenido de la primera.",
        "ACUERDO No. 008\nContenido de la segunda.",
        "ACUERDO No. 008\nContenido de la tercera.",
    ]

    resultado = Chunker._strip_repeated_lines(paginas)

    assert "ACUERDO No. 008" in resultado[0]
    assert "ACUERDO No. 008" not in resultado[1]
    assert "ACUERDO No. 008" not in resultado[2]
    # El contenido propio de cada pagina no se toca.
    assert "Contenido de la segunda." in resultado[1]


def test_strip_repeated_lines_no_toca_un_documento_de_una_sola_pagina():
    # Sin varias paginas no hay forma de saber que es encabezado y que es contenido.
    paginas = ["Linea repetida\nLinea repetida"]

    assert Chunker._strip_repeated_lines(paginas) == paginas


def test_split_pages_numera_desde_uno_y_no_desplaza_al_saltar_vacias():
    chunker = Chunker(chunk_size=200, chunk_overlap=0)

    documentos = chunker.split_pages(["Texto de la primera.", "   ", "Texto de la tercera."])

    # La pagina 2 esta vacia: no genera chunks, pero la 3 sigue siendo la 3.
    assert [documento.metadata["page"] for documento in documentos] == [1, 3]


def test_split_respeta_el_tamano_maximo_de_chunk():
    chunker = Chunker(chunk_size=60, chunk_overlap=0)
    texto = " ".join(f"Frase numero {i} con algo de relleno." for i in range(20))

    assert all(len(chunk) <= 60 for chunk in chunker.split(texto))


def test_un_solape_de_cero_se_respeta_y_no_cae_en_la_configuracion():
    # Con `or`, el 0 se confundiria con "no indicado" y volveria el valor del .env.
    chunker = Chunker(chunk_size=60, chunk_overlap=0)

    assert chunker.splitter._chunk_overlap == 0
