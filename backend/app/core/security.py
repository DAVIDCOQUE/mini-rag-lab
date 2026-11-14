import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.config import settings

_MAINTAINER_USERNAME = "mantenedor"
_basic_auth = HTTPBasic(auto_error=False)


def require_maintainer(
    credentials: Annotated[HTTPBasicCredentials | None, Depends(_basic_auth)],
) -> None:
    password = settings.MAINTAINER_PASSWORD.get_secret_value()
    if len(password) < 16:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Configura MAINTAINER_PASSWORD con al menos 16 caracteres.",
        )

    if credentials is None:
        raise _unauthorized()

    valid_username = secrets.compare_digest(
        credentials.username.encode("utf-8"), _MAINTAINER_USERNAME.encode("utf-8")
    )
    valid_password = secrets.compare_digest(
        credentials.password.encode("utf-8"), password.encode("utf-8")
    )
    if not (valid_username and valid_password):
        raise _unauthorized()


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Usuario o contraseña incorrectos.",
        headers={"WWW-Authenticate": 'Basic realm="mantenedor"'},
    )
