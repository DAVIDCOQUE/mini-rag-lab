from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.security import require_maintainer

router = APIRouter(tags=["auth"])


@router.get("/auth/verify")
def verify_maintainer(
    _: Annotated[None, Depends(require_maintainer)],
) -> dict[str, bool]:
    return {"authenticated": True}
