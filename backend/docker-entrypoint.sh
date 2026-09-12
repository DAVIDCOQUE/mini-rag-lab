#!/bin/sh
set -e

# El esquema tiene que existir antes de que la app abra conexiones. Alembic es
# idempotente, asi que repetirlo en cada arranque no cuesta nada.
alembic upgrade head

exec "$@"
