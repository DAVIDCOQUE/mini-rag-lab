import logging
import re
import uuid
from collections.abc import Sequence
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.rag import llm_service
from app.rag.embedding_service import EmbeddingService
from app.rag.llm_service import LLMError
from app.rag.query_router import _cosine
from app.repositories import document_repository

logger = logging.getLogger("mini_rag_lab")

# Mas de unos pocos QR a la vez confunde en la pantalla del quiosco.
MAX_FORMS = 3
# Solo embeddings: distancia maxima al mejor formato para ofrecer tambien otro.
FORM_MATCH_MARGIN = 0.05
# Candidatos que se le muestran al LLM para confirmar.
MAX_CANDIDATES = 5

# Con embeddings, "cancelar el semestre" y "cancelar una materia" quedan demasiado
# cerca: sin esta confirmacion se ofrecia el formato del semestre a quien pedia una materia.
# Se juzga cada formato por separado y sin ejemplos concretos: con un ejemplo en el prompt,
# llama3.1:8b lo repetia como respuesta aunque la pregunta fuera otra.
CONFIRM_PROMPT = """Eres el asistente de un quiosco universitario. El estudiante pregunta por un tramite y hay unos formatos candidatos. Evalua cada formato por separado: "serves" es true solo si el formato es para el mismo tramite que pide el estudiante, y false si es para otro tramite, aunque se parezca. Para cada formato escribe primero "reason" (una frase) y luego "serves"."""

CONFIRM_SCHEMA = {
    "type": "object",
    "properties": {
        "evaluations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "form": {"type": "integer"},
                    "reason": {"type": "string"},
                    "serves": {"type": "boolean"},
                },
                "required": ["form", "reason", "serves"],
            },
        }
    },
    "required": ["evaluations"],
}


class FormMatcher:
    """Elige que formatos ofrecer a partir de la descripcion que escribio el administrador.

    Los formatos no estan en Qdrant: son pocos, asi que sus descripciones se embeben
    una vez y se guardan en memoria. Se vuelven a embeber solo las que cambian.
    """

    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()
        # id -> (descripcion embebida, vector). La descripcion hace de clave: si el
        # administrador la edita, el vector viejo deja de valer.
        self._vectors: dict[uuid.UUID, tuple[str, list[float]]] = {}

    def match(
        self,
        db: Session,
        question: str,
        query_vector: list[float],
        answer: str | None = None,
        context: str = "",
    ) -> list[tuple[Document, float]]:
        """Formatos que sirven para la pregunta.

        Primero por codigo: si la respuesta cita el codigo de un formato (la guia dice
        "diligenciar el formato R-GA002"), se ofrece ese. Si no, por descripcion.
        """
        forms = document_repository.list_forms(db)
        cited = cited_forms(forms, answer, context)
        if cited:
            return [(form, 1.0) for form in cited][:MAX_FORMS]

        stale = [form for form in forms if self._vectors.get(form.id, ("",))[0] != form.description]
        if stale:
            vectors = self.embedding_service.embed([form.description for form in stale])
            for form, vector in zip(stale, vectors):
                self._vectors[form.id] = (form.description, vector)
            logger.info("Descripciones de formatos embebidas: %d", len(stale))

        scored = sorted(
            ((form, _cosine(query_vector, self._vectors[form.id][1])) for form in forms),
            key=lambda pair: pair[1],
            reverse=True,
        )
        if settings.ROUTER_MODE == "llm":
            return confirm_with_llm(question, scored)
        return choose_by_similarity(scored)


def _compact(text: str) -> str:
    """Solo letras y digitos en mayuscula: "R-GA 004" y "r-ga004" valen igual."""
    return re.sub(r"[^0-9A-Z]", "", text.upper())


def cited_forms(forms: Sequence[Document], answer: str | None, context: str) -> list[Document]:
    """Formatos cuyo codigo cita la respuesta y aparece tambien en los fragmentos usados.

    Exigirlo en ambos sitios evita que un codigo inventado por el modelo dispare un
    formato que la guia no menciona para ese tramite.
    """
    if not answer:
        return []
    said, grounded = _compact(answer), _compact(context)
    return [
        form
        for form in forms
        if form.form_code and _compact(form.form_code) in said and _compact(form.form_code) in grounded
    ]


def choose_by_similarity(scored: list[tuple[Document, float]]) -> list[tuple[Document, float]]:
    """Sin LLM: el mejor si supera el umbral, y los que queden muy cerca de el."""
    if not scored or scored[0][1] < settings.FORM_MATCH_MIN_SCORE:
        return []
    floor = max(settings.FORM_MATCH_MIN_SCORE, scored[0][1] - FORM_MATCH_MARGIN)
    return [(form, score) for form, score in scored if score >= floor][:MAX_FORMS]


def confirm_with_llm(question: str, scored: list[tuple[Document, float]]) -> list[tuple[Document, float]]:
    """Los embeddings preseleccionan con un umbral bajo; el LLM decide cuales sirven."""
    candidates = [pair for pair in scored if pair[1] >= settings.FORM_CANDIDATE_MIN_SCORE][:MAX_CANDIDATES]
    if not candidates:
        return []

    listing = "\n".join(f"{i}. {form.description}" for i, (form, _) in enumerate(candidates, start=1))
    messages = [
        {"role": "system", "content": CONFIRM_PROMPT},
        {"role": "user", "content": f"Pregunta: {question}\n\nFormatos:\n{listing}"},
    ]
    try:
        data = llm_service.chat_structured(messages, CONFIRM_SCHEMA, timeout=settings.ROUTER_LLM_TIMEOUT_S)
    except LLMError as exc:
        # Ofrecer un formato equivocado es peor que no ofrecer ninguno.
        logger.warning("No se pudo confirmar el formato con el LLM (%s); no se ofrece ninguno.", exc)
        return []

    chosen = {
        item.get("form")
        for item in data.get("evaluations", [])
        if item.get("serves") is True and isinstance(item.get("form"), int) and 1 <= item["form"] <= len(candidates)
    }
    return [candidates[n - 1] for n in sorted(chosen)][:MAX_FORMS]


def display_name(form: Document) -> str:
    """Nombre con el que se ofrece el formato: codigo y titulo legible del archivo."""
    title = re.sub(r"[_\-]+", " ", Path(form.original_name).stem).strip().capitalize()
    return f"{form.form_code} ({title})" if form.form_code else title


def offered_in(forms: Sequence[Document], text: str) -> list[Document]:
    """Formatos que se ofrecieron en un mensaje del asistente.

    El backend no guarda la conversacion: lo ofrecido se recupera del texto de la oferta,
    que lleva el nombre exacto de display_name.
    """
    return [form for form in forms if display_name(form) in text]
