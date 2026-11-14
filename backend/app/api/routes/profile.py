from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.profile import ProfileResponse, ProfileUpdate
from app.services import profile_service
from app.services.profile_service import InvalidProfileError

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
def get_profile(db: Session = Depends(get_db)) -> ProfileResponse:
    return profile_service.get_profile(db)


@router.put("", response_model=ProfileResponse)
def update_profile(payload: ProfileUpdate, db: Session = Depends(get_db)) -> ProfileResponse:
    try:
        return profile_service.update_profile(db, payload)
    except InvalidProfileError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
