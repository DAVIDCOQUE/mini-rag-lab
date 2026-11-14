"""Inicio de sesion unico en OneDrive para el modo de cuenta personal (ONEDRIVE_MODE=user).

Uso, desde backend/:  python -m scripts.onedrive_login
Muestra un codigo y una URL; al iniciar sesion en el navegador, el token queda en
ONEDRIVE_TOKEN_CACHE y el backend lo renueva solo.
"""

import sys

from app.core.config import settings
from app.services.onedrive_service import USER_SCOPES, load_token_cache, public_app, save_token_cache


def main() -> int:
    if settings.ONEDRIVE_MODE != "user" or not settings.ONEDRIVE_CLIENT_ID:
        print("Configura ONEDRIVE_MODE=user y ONEDRIVE_CLIENT_ID en el .env primero.")
        return 1

    cache = load_token_cache()
    app = public_app(cache)
    flow = app.initiate_device_flow(scopes=USER_SCOPES)
    if "user_code" not in flow:
        print(f"No se pudo iniciar el login: {flow.get('error_description')}")
        return 1

    print(flow["message"])
    result = app.acquire_token_by_device_flow(flow)
    if "access_token" not in result:
        print(f"Login fallido: {result.get('error_description')}")
        return 1

    save_token_cache(cache)
    account = result.get("id_token_claims", {}).get("preferred_username", "la cuenta")
    print(f"Listo: sesion guardada para {account} en {settings.ONEDRIVE_TOKEN_CACHE}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
