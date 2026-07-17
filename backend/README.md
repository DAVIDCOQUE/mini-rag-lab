# Mini RAG Lab — Backend (FastAPI)

## Requisitos
- Python 3.12 (recomendado). El venv incluido usa la version disponible en la maquina.
- PostgreSQL en ejecucion (solo necesario para migraciones/DB, no para `/health`).

## Puesta en marcha

```bash
# 1. Activar el entorno virtual
.venv\Scripts\activate        # Windows (PowerShell/CMD)

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Copiar variables de entorno
copy .env.example .env        # ajustar DATABASE_URL si aplica

# 4. Levantar el servidor
uvicorn app.main:app --reload
```

- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Migraciones (Alembic)

```bash
alembic revision --autogenerate -m "mensaje"
alembic upgrade head
```

## Estructura

```
app/
  api/routes/     Endpoints HTTP
  core/           Configuracion (Pydantic Settings)
  database/       Engine, sesion y Base declarativa
  models/         Modelos ORM (SQLAlchemy)
  schemas/        DTOs (Pydantic)
  repositories/   Acceso a datos
  services/       Logica de negocio
  rag/            Modulo RAG (pendiente en clases futuras)
  utils/          Utilidades
  main.py         Punto de entrada FastAPI
```
