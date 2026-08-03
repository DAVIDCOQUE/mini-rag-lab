import logging
from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.models.prompt_template import PromptTemplate
from app.rag.prompt_builder import (
    DEFAULT_PROMPT_CODE,
    DEFAULT_PROMPT_NAME,
    NO_ANSWER_MESSAGE,
    NO_ANSWER_PLACEHOLDER,
    SYSTEM_PROMPT_TEMPLATE,
)
from app.repositories import prompt_template_repository as repository
from app.schemas.prompt import DefaultPrompt, PromptTemplateCreate, PromptTemplateUpdate

logger = logging.getLogger("mini_rag_lab")


class PromptNotFoundError(Exception):
    """La variante de prompt solicitada no existe."""


class PromptCodeTakenError(Exception):
    """Ya existe una variante con ese code."""


def default_prompt() -> DefaultPrompt:
    """El prompt del repositorio, tal cual esta en el codigo, como referencia de la UI."""
    return DefaultPrompt(
        code=DEFAULT_PROMPT_CODE,
        name=DEFAULT_PROMPT_NAME,
        body=SYSTEM_PROMPT_TEMPLATE,
        no_answer_placeholder=NO_ANSWER_PLACEHOLDER,
        no_answer_message=NO_ANSWER_MESSAGE,
    )


def list_templates(db: Session) -> Sequence[PromptTemplate]:
    return repository.list_all(db)


def get_template(db: Session, code: str) -> PromptTemplate:
    template = repository.get_by_code(db, code)
    if template is None:
        raise PromptNotFoundError
    return template


def create_template(db: Session, payload: PromptTemplateCreate) -> PromptTemplate:
    # El code del repositorio esta reservado: dejar crearlo haria ambiguo a que
    # prompt se refiere una peticion.
    if payload.code == DEFAULT_PROMPT_CODE or repository.get_by_code(db, payload.code):
        raise PromptCodeTakenError

    template = PromptTemplate(code=payload.code, name=payload.name, body=payload.body)
    template = repository.create(db, template)
    logger.info("Prompt creado: %s (%s)", template.name, template.code)
    return template


def update_template(db: Session, code: str, payload: PromptTemplateUpdate) -> PromptTemplate:
    template = get_template(db, code)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(template, field, value)
    return repository.update(db, template)


def delete_template(db: Session, code: str) -> None:
    """Borra la variante. Si era la activa, el sistema vuelve al prompt del repositorio."""
    template = get_template(db, code)
    was_active = template.is_active
    repository.delete(db, template)
    logger.info("Prompt eliminado: %s%s", code, " (estaba activo)" if was_active else "")


def activate_template(db: Session, code: str) -> PromptTemplate:
    """Deja activa solo la variante indicada."""
    template = get_template(db, code)
    repository.deactivate_all(db)
    template.is_active = True
    return repository.update(db, template)


def deactivate_all(db: Session) -> None:
    """Vuelve al prompt del repositorio sin borrar ninguna variante."""
    repository.deactivate_all(db)
    db.commit()


def resolve_prompt(db: Session, code: str | None = None) -> tuple[str | None, str]:
    """Instrucciones a usar y code del prompt del que salieron.

    - code explicito: esa variante (o el del repositorio si piden 'default').
    - sin code: la variante activa si la hay; si no, el del repositorio.

    Devuelve None como cuerpo cuando toca el prompt del repositorio, que es lo que
    build_prompt interpreta como "usa el tuyo".
    """
    if code == DEFAULT_PROMPT_CODE:
        return None, DEFAULT_PROMPT_CODE

    if code:
        template = get_template(db, code)
        return template.body, template.code

    active = repository.get_active(db)
    if active is None:
        return None, DEFAULT_PROMPT_CODE
    return active.body, active.code
