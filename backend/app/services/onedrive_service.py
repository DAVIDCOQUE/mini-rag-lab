import logging
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

import httpx

from app.core.config import settings

logger = logging.getLogger("mini_rag_lab")

GRAPH_URL = "https://graph.microsoft.com/v1.0"
APP_SCOPES = ["https://graph.microsoft.com/.default"]
# offline_access lo agrega MSAL solo; pedirlo explicito hace fallar la llamada.
USER_SCOPES = ["Files.ReadWrite"]
TIMEOUT_S = 120.0


class CloudStorageError(Exception):
    """No se pudo subir el formato o crear su enlace publico. El mensaje es para el usuario."""


@dataclass
class CloudFile:
    item_id: str
    public_url: str


def is_enabled() -> bool:
    return bool(settings.ONEDRIVE_MODE and settings.ONEDRIVE_CLIENT_ID)


def upload_form(filename: str, content: bytes, item_id: str | None = None) -> CloudFile:
    """Sube el PDF y devuelve su enlace de solo lectura para cualquiera.

    Con item_id se reemplaza el contenido de ese archivo: el enlace no cambia, asi que los
    QR ya impresos siguen llevando al formato actualizado.
    """
    if not is_enabled():
        raise CloudStorageError("La subida a OneDrive no está configurada.")
    headers = {"Authorization": f"Bearer {_access_token()}"}
    drive = _drive_path()

    with httpx.Client(timeout=TIMEOUT_S, headers=headers) as client:
        if item_id:
            session_url = f"{GRAPH_URL}{drive}/items/{item_id}/createUploadSession"
        else:
            path = quote(f"{settings.ONEDRIVE_FOLDER.strip('/')}/{filename}")
            session_url = f"{GRAPH_URL}{drive}/root:/{path}:/createUploadSession"
        # Sesion de subida en vez del PUT simple: este se limita a 4 MB y los PDF admiten 20.
        body = {"item": {"@microsoft.graph.conflictBehavior": "rename"}} if not item_id else {}
        session = _call(client, "post", session_url, json=body, action="iniciar la subida")
        upload_url = session["uploadUrl"]

        # La URL de la sesion ya va firmada: llevar el token de Graph la hace fallar.
        size = len(content)
        response = httpx.put(
            upload_url,
            content=content,
            headers={"Content-Length": str(size), "Content-Range": f"bytes 0-{size - 1}/{size}"},
            timeout=TIMEOUT_S,
        )
        if response.status_code not in (200, 201):
            logger.warning("OneDrive rechazo el archivo: %s %s", response.status_code, response.text[:300])
            raise CloudStorageError("OneDrive rechazó el archivo.")
        new_id = response.json()["id"]

        link = _call(
            client,
            "post",
            f"{GRAPH_URL}{drive}/items/{new_id}/createLink",
            json={"type": "view", "scope": "anonymous"},
            action="crear el enlace público",
        )
    logger.info("Formato subido a OneDrive: %s (%s)", filename, new_id)
    return CloudFile(item_id=new_id, public_url=link["link"]["webUrl"])


def _call(client: httpx.Client, method: str, url: str, action: str, **kwargs) -> dict:
    try:
        response = client.request(method, url, **kwargs)
    except httpx.HTTPError as exc:
        logger.warning("OneDrive no responde al %s: %s", action, exc)
        raise CloudStorageError("No se pudo conectar con OneDrive.") from exc
    if response.status_code >= 400:
        logger.warning("OneDrive fallo al %s: %s %s", action, response.status_code, response.text[:300])
        # Un tenant con los enlaces anonimos desactivados responde asi al crear el enlace.
        if "createLink" in url and response.status_code in (400, 403):
            raise CloudStorageError(
                "El archivo se subió, pero la cuenta no permite enlaces públicos. "
                "Pide a TI que habilite los vínculos de 'Cualquier persona'."
            )
        raise CloudStorageError(f"No se pudo {action} en OneDrive ({response.status_code}).")
    return response.json()


def _drive_path() -> str:
    if settings.ONEDRIVE_MODE == "app":
        if not settings.ONEDRIVE_DRIVE_USER:
            raise CloudStorageError("Falta ONEDRIVE_DRIVE_USER: la cuenta cuyo OneDrive guarda los formatos.")
        return f"/users/{quote(settings.ONEDRIVE_DRIVE_USER)}/drive"
    return "/me/drive"


def _access_token() -> str:
    import msal

    if settings.ONEDRIVE_MODE == "app":
        app = msal.ConfidentialClientApplication(
            settings.ONEDRIVE_CLIENT_ID,
            authority=f"https://login.microsoftonline.com/{settings.ONEDRIVE_TENANT_ID}",
            client_credential=settings.ONEDRIVE_CLIENT_SECRET,
        )
        result = app.acquire_token_for_client(scopes=APP_SCOPES)
    else:
        cache = load_token_cache()
        app = public_app(cache)
        accounts = app.get_accounts()
        result = app.acquire_token_silent(USER_SCOPES, account=accounts[0]) if accounts else None
        if not result:
            raise CloudStorageError(
                "No hay sesión de OneDrive. Ejecuta `python -m scripts.onedrive_login` desde backend/."
            )
        save_token_cache(cache)

    if "access_token" not in result:
        logger.warning("OneDrive no entrego token: %s", result.get("error_description"))
        raise CloudStorageError("No se pudo autenticar con OneDrive. Revisa las credenciales del .env.")
    return result["access_token"]


# --- Cuenta personal: cache del token compartida con scripts/onedrive_login.py ---


def public_app(cache):
    import msal

    return msal.PublicClientApplication(
        settings.ONEDRIVE_CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{settings.ONEDRIVE_TENANT_ID}",
        token_cache=cache,
    )


def load_token_cache():
    import msal

    cache = msal.SerializableTokenCache()
    path = Path(settings.ONEDRIVE_TOKEN_CACHE)
    if path.is_file():
        cache.deserialize(path.read_text(encoding="utf-8"))
    return cache


def save_token_cache(cache) -> None:
    # MSAL renueva el token en silencio: sin guardarlo, el refresh token nuevo se perderia.
    if cache.has_state_changed:
        path = Path(settings.ONEDRIVE_TOKEN_CACHE)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(cache.serialize(), encoding="utf-8")
