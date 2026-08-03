from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.prompt import (
    DefaultPrompt,
    PromptTemplateCreate,
    PromptTemplateRead,
    PromptTemplateUpdate,
)
from app.services import prompt_service as service
from app.services.prompt_service import PromptCodeTakenError, PromptNotFoundError

router = APIRouter(prefix="/prompts", tags=["prompts"])

NOT_FOUND_DETAIL = "Prompt no encontrado."


# Declarada antes que /{code} para que el path param no se coma la ruta.
@router.get("/default", response_model=DefaultPrompt)
def get_default_prompt() -> DefaultPrompt:
    """Prompt del repositorio: referencia de solo lectura para crear variantes."""
    return service.default_prompt()


@router.get("", response_model=list[PromptTemplateRead])
def list_prompts(db: Session = Depends(get_db)) -> list[PromptTemplateRead]:
    return service.list_templates(db)


@router.post("", response_model=PromptTemplateRead, status_code=status.HTTP_201_CREATED)
def create_prompt(payload: PromptTemplateCreate, db: Session = Depends(get_db)) -> PromptTemplateRead:
    try:
        return service.create_template(db, payload)
    except PromptCodeTakenError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un prompt con ese código.",
        )


@router.get("/{code}", response_model=PromptTemplateRead)
def get_prompt(code: str, db: Session = Depends(get_db)) -> PromptTemplateRead:
    try:
        return service.get_template(db, code)
    except PromptNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND_DETAIL)


@router.patch("/{code}", response_model=PromptTemplateRead)
def update_prompt(
    code: str, payload: PromptTemplateUpdate, db: Session = Depends(get_db)
) -> PromptTemplateRead:
    try:
        return service.update_template(db, code, payload)
    except PromptNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND_DETAIL)


@router.delete("/{code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prompt(code: str, db: Session = Depends(get_db)) -> None:
    try:
        service.delete_template(db, code)
    except PromptNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND_DETAIL)


@router.post("/default/activate", status_code=status.HTTP_204_NO_CONTENT)
def activate_default_prompt(db: Session = Depends(get_db)) -> None:
    """Vuelve al prompt del repositorio sin borrar ninguna variante."""
    service.deactivate_all(db)


@router.post("/{code}/activate", response_model=PromptTemplateRead)
def activate_prompt(code: str, db: Session = Depends(get_db)) -> PromptTemplateRead:
    """Deja este prompt como el que usa el chat."""
    try:
        return service.activate_template(db, code)
    except PromptNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND_DETAIL)
