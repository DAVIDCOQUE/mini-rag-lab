import uuid
from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.rag import form_matcher as fm
from app.schemas.document import DocumentKind
from app.services import document_service
from app.services.document_processing_service import DocumentProcessingService, FormNotIndexableError
from app.services.document_service import InvalidDocumentError


def _form(description: str):
    return SimpleNamespace(id=uuid.uuid4(), description=description, original_name=f"{description}.pdf")


def _matcher(monkeypatch, forms, vectors: dict[str, list[float]]):
    """Matcher sin LLM con formatos y embeddings inyectados, sin base de datos ni Ollama."""
    monkeypatch.setattr(settings, "ROUTER_MODE", "embedding")
    monkeypatch.setattr(fm.document_repository, "list_forms", lambda db: forms)
    matcher = fm.FormMatcher()
    calls: list[list[str]] = []

    def embed(texts):
        calls.append(texts)
        return [vectors[text] for text in texts]

    monkeypatch.setattr(matcher.embedding_service, "embed", embed)
    return matcher, calls


def test_ofrece_el_formato_que_se_parece_a_la_pregunta(monkeypatch):
    monkeypatch.setattr(settings, "FORM_MATCH_MIN_SCORE", 0.6)
    semestre, cursos = _form("cancelar semestre"), _form("cancelar cursos")
    matcher, _ = _matcher(monkeypatch, [semestre, cursos], {"cancelar semestre": [1.0, 0.0], "cancelar cursos": [0.0, 1.0]})

    elegidos = matcher.match(None, "pregunta", [0.95, 0.31])

    assert [form for form, _ in elegidos] == [semestre]


def test_sin_formato_suficientemente_parecido_no_ofrece_ninguno(monkeypatch):
    monkeypatch.setattr(settings, "FORM_MATCH_MIN_SCORE", 0.6)
    matcher, _ = _matcher(monkeypatch, [_form("cancelar semestre")], {"cancelar semestre": [1.0, 0.0]})

    assert matcher.match(None, "pregunta", [0.5, 0.87]) == []


def test_dos_formatos_casi_empatados_se_ofrecen_ambos(monkeypatch):
    # Pregunta ambigua ("quiero retirarme"): mejor ofrecer los dos que adivinar.
    monkeypatch.setattr(settings, "FORM_MATCH_MIN_SCORE", 0.6)
    a, b = _form("a"), _form("b")
    matcher, _ = _matcher(monkeypatch, [a, b], {"a": [1.0, 0.0], "b": [0.0, 1.0]})

    elegidos = matcher.match(None, "pregunta", [0.72, 0.69])

    assert {form.id for form, _ in elegidos} == {a.id, b.id}


def test_solo_se_reembeben_las_descripciones_que_cambian(monkeypatch):
    form = _form("cancelar semestre")
    matcher, calls = _matcher(
        monkeypatch, [form], {"cancelar semestre": [1.0, 0.0], "retiro del semestre": [1.0, 0.0]}
    )

    matcher.match(None, "pregunta", [1.0, 0.0])
    matcher.match(None, "pregunta", [1.0, 0.0])
    form.description = "retiro del semestre"
    matcher.match(None, "pregunta", [1.0, 0.0])

    assert calls == [["cancelar semestre"], ["retiro del semestre"]]


def test_un_formato_sin_descripcion_no_se_acepta():
    with pytest.raises(InvalidDocumentError):
        document_service._clean_description(DocumentKind.FORM, "   ")


def test_un_documento_de_informacion_no_necesita_descripcion():
    assert document_service._clean_description(DocumentKind.KNOWLEDGE, "  ") is None


def test_un_formato_no_se_puede_indexar(monkeypatch):
    form = SimpleNamespace(id=uuid.uuid4(), kind=DocumentKind.FORM.value)
    monkeypatch.setattr(document_service, "get_document", lambda db, document_id: form)

    with pytest.raises(FormNotIndexableError):
        DocumentProcessingService().index_document(None, form.id)


def _confirma(monkeypatch, evaluaciones):
    monkeypatch.setattr(settings, "FORM_CANDIDATE_MIN_SCORE", 0.5)
    monkeypatch.setattr(fm.llm_service, "chat_structured", lambda messages, schema, timeout: {"evaluations": evaluaciones})


def test_el_llm_descarta_un_formato_parecido_pero_de_otro_tramite(monkeypatch):
    semestre = _form("cancelar semestre")
    _confirma(monkeypatch, [{"form": 1, "reason": "es otro tramite", "serves": False}])

    assert fm.confirm_with_llm("¿Cómo cancelo una materia?", [(semestre, 0.64)]) == []


def test_el_llm_confirma_el_formato_que_sirve(monkeypatch):
    semestre, cursos = _form("cancelar semestre"), _form("cancelar cursos")
    _confirma(
        monkeypatch,
        [{"form": 1, "reason": "-", "serves": False}, {"form": 2, "reason": "-", "serves": True}],
    )

    elegidos = fm.confirm_with_llm("¿Cómo cancelo una materia?", [(semestre, 0.75), (cursos, 0.72)])

    assert [form for form, _ in elegidos] == [cursos]


def test_sin_candidatos_no_se_llama_al_llm(monkeypatch):
    monkeypatch.setattr(settings, "FORM_CANDIDATE_MIN_SCORE", 0.5)

    def no_llamar(*args, **kwargs):
        raise AssertionError("no deberia llamarse al LLM")

    monkeypatch.setattr(fm.llm_service, "chat_structured", no_llamar)

    assert fm.confirm_with_llm("¿Quién es el rector?", [(_form("certificado"), 0.3)]) == []


def test_si_el_llm_falla_no_se_ofrece_ninguno(monkeypatch):
    monkeypatch.setattr(settings, "FORM_CANDIDATE_MIN_SCORE", 0.5)

    def falla(*args, **kwargs):
        raise fm.LLMError("timeout")

    monkeypatch.setattr(fm.llm_service, "chat_structured", falla)

    assert fm.confirm_with_llm("¿Cómo cancelo el semestre?", [(_form("cancelar semestre"), 0.82)]) == []


def test_un_numero_de_formato_inventado_se_ignora(monkeypatch):
    _confirma(monkeypatch, [{"form": 7, "reason": "-", "serves": True}])

    assert fm.confirm_with_llm("x", [(_form("a"), 0.9)]) == []


def _coded(code: str | None, description: str = "x"):
    return SimpleNamespace(id=uuid.uuid4(), description=description, original_name=f"{code}.pdf", form_code=code)


def test_se_ofrece_el_formato_cuyo_codigo_cita_la_respuesta():
    semestre, matricula = _coded("R-GA004"), _coded("R-GA002")
    guia = "Cancelación de Cursos. REQUISITOS: Diligenciar formato R-GA002 y radicarlo."

    elegidos = fm.cited_forms([semestre, matricula], "Debes diligenciar el formato R-GA002.", guia)

    assert elegidos == [matricula]


def test_el_codigo_se_reconoce_con_otra_escritura():
    form = _coded("R-GA004")

    assert fm.cited_forms([form], "llena el formato r-ga 004", "formato R-GA004") == [form]


def test_un_codigo_que_no_esta_en_la_guia_no_cuenta():
    # El modelo podria inventar un codigo: sin respaldo en los fragmentos no se ofrece.
    form = _coded("R-GA004")

    assert fm.cited_forms([form], "Usa el formato R-GA004.", "texto sin codigos") == []


def test_un_formato_sin_codigo_nunca_se_elige_por_codigo():
    assert fm.cited_forms([_coded(None)], "formato R-GA004", "formato R-GA004") == []


def test_sin_codigo_citado_decide_la_descripcion(monkeypatch):
    monkeypatch.setattr(settings, "ROUTER_MODE", "embedding")
    monkeypatch.setattr(settings, "FORM_MATCH_MIN_SCORE", 0.6)
    form = _coded(None, "cancelar semestre")
    monkeypatch.setattr(fm.document_repository, "list_forms", lambda db: [form])
    matcher = fm.FormMatcher()
    monkeypatch.setattr(matcher.embedding_service, "embed", lambda texts: [[1.0, 0.0]])

    elegidos = matcher.match(None, "q", [1.0, 0.0], answer="Respuesta sin codigos.", context="guia")

    assert [f for f, _ in elegidos] == [form]


def test_lee_el_codigo_impreso_en_el_pdf(tmp_path):
    import fitz

    path = tmp_path / "formato.pdf"
    pdf = fitz.open()
    pdf.new_page().insert_text((72, 72), "UNIVERSIDAD SANTIAGO DE CALI  CODIGO: R-GA004  VERSION: 3")
    pdf.save(path)

    assert document_service._extract_code(path) == "R-GA004"


def test_un_pdf_sin_codigo_lo_deja_vacio(tmp_path):
    import fitz

    path = tmp_path / "formato.pdf"
    pdf = fitz.open()
    pdf.new_page().insert_text((72, 72), "Nombre: ______  Firma: ______")
    pdf.save(path)

    assert document_service._extract_code(path) is None


from app.rag import prompt_builder as pb


def test_el_nombre_ofrecido_lleva_codigo_y_titulo():
    form = SimpleNamespace(original_name="FORMATO_DE_CANCELACION_DE_SEMESTRE.pdf", form_code="R-GA004")

    assert fm.display_name(form) == "R-GA004 (Formato de cancelacion de semestre)"


def test_lo_ofrecido_se_recupera_del_mensaje_del_asistente():
    semestre = SimpleNamespace(original_name="Cancelacion.pdf", form_code="R-GA004")
    otro = SimpleNamespace(original_name="Otro.pdf", form_code="R-GA001")
    oferta = f"Debes radicarlo.\n\n{pb.form_offer([fm.display_name(semestre)])}"

    assert fm.offered_in([semestre, otro], oferta) == [semestre]


@pytest.mark.parametrize("mensaje", ["sí", "Si porfa", "dale", "claro que sí", "ok", "pásamelo"])
def test_reconoce_la_aceptacion(mensaje):
    assert pb.is_affirmative(mensaje)


@pytest.mark.parametrize("mensaje", ["no gracias", "sí, pero ¿cómo cancelo solo un curso y no todo el semestre?", "¿Quién es el rector?"])
def test_no_toma_por_aceptacion_otra_cosa(mensaje):
    assert not pb.is_affirmative(mensaje)


def test_pedir_el_formato_directamente():
    assert pb.asks_for_form("Pásame el formato de cancelación")
    assert not pb.asks_for_form("¿Cómo cancelo el semestre?")
