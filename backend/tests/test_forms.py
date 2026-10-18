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
