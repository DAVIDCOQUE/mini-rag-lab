"""Genera el valor de ADMIN_PASSWORD_HASH para el .env.

Uso, desde backend/:  python -m scripts.hash_password
Pide la contrasena sin mostrarla y la confirma. La contrasena nunca se guarda en claro.
"""

import getpass
import sys

from app.services.auth_service import hash_password

MIN_LENGTH = 10


def main() -> int:
    password = getpass.getpass("Contraseña del mantenedor: ")
    if len(password) < MIN_LENGTH:
        print(f"Usa al menos {MIN_LENGTH} caracteres.")
        return 1
    if getpass.getpass("Repítela: ") != password:
        print("No coinciden.")
        return 1
    print("\nAgrega esta línea al backend/.env y reinicia el backend:\n")
    print(f"ADMIN_PASSWORD_HASH={hash_password(password)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
