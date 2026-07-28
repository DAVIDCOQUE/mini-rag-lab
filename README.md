# Mini RAG Lab

Laboratorio de aprendizaje para construir un sistema RAG paso a paso.
En esta etapa solo está preparada la **infraestructura**: backend FastAPI, frontend Angular,
y la estructura vacía para RAG/documentos. Todavía **no** hay IA, embeddings, Qdrant ni PDFs implementados.

---

## Requisitos

| Herramienta | Versión sugerida |
|---|---|
| Python | 3.12 |
| Node.js | 20+ |
| Angular CLI | 20 |
| PostgreSQL | 16 (opcional en esta etapa) |
| Qdrant | se descarga con `scripts\setup-qdrant.ps1` |
| Ollama | (para clases futuras) |

---

## Cómo levantar el backend (FastAPI)

```bash
cd backend

# 1. Crear y activar entorno virtual
python -m venv .venv
.venv\Scripts\activate        # Windows

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Copiar variables de entorno
copy .env.example .env        # ajustar credenciales si aplica

# 4. Levantar el servidor (usa HOST/PORT del .env)
python -m app.main
# o, con recarga en caliente y sin log de acceso duplicado de uvicorn:
uvicorn app.main:app --reload --no-access-log
```

- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

El health check responde:

```json
{
  "status": "ok",
  "service": "Mini RAG Lab",
  "version": "1.0.0",
  "database": "pending",
  "qdrant": "pending",
  "ollama": "pending"
}
```

---

## Cómo levantar el frontend (Angular)

```bash
cd frontend

# 1. Instalar dependencias
npm install

# 2. Levantar el servidor de desarrollo (proxy hacia FastAPI ya configurado)
npm start
```

- App: http://localhost:4200

En desarrollo, Angular usa `proxy.conf.json` para reenviar `/health` y `/api` hacia
`http://localhost:8000`. Así el navegador trabaja en el mismo origen y **no hay problemas de CORS**.
Al abrir la app debe aparecer: **✅ Backend conectado correctamente** (consumiendo `/health` real).

---

## Cómo ejecutar Qdrant

El binario **no está versionado en git** (pesa 82 MB y es solo Windows). Hay un script que lo descarga:

```powershell
# desde la raíz del repo, una sola vez
.\scripts\setup-qdrant.ps1

# arrancar
.\qdrant-x86_64-pc-windows-msvc\qdrant.exe
```

El script descarga el binario (`v1.18.2`) y el dashboard web (`v0.2.15`) desde GitHub Releases.
Es idempotente: si ya están, no vuelve a descargar. Para actualizar Qdrant, cambia
`$QdrantVersion` en el script y borra el `qdrant.exe` anterior.

- REST API: http://localhost:6333
- Dashboard: http://localhost:6333/dashboard

> En Mac/Linux el script no aplica: descarga el asset correspondiente desde
> https://github.com/qdrant/qdrant/releases o levanta la imagen `qdrant/qdrant` con Docker.

---

## Base de datos (PostgreSQL)

El repo **no impone** cómo levantar PostgreSQL: instalación local, contenedor Docker o
instancia remota, lo que prefieras. Solo tiene que ser accesible con las credenciales de
`backend/.env` (`POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`).

Una vez apunte a tu instancia, crea el esquema:

```bash
cd backend
alembic upgrade head
```

> El backend usa SQLAlchemy con el driver `psycopg2`, así que el motor debe ser PostgreSQL;
> lo abierto es *dónde* corre, no *qué* motor es.

---

## Cómo ejecutar Ollama

```bash
# 1. Instalar desde https://ollama.com
# 2. Iniciar el servicio
ollama serve

# 3. (Futuro) descargar un modelo
ollama pull llama3
```

- API: http://localhost:11434

> Aún no se usa desde el backend; se integrará en clases futuras.

---

## Estructura del proyecto

```
mini-rag-lab/
├── backend/                     FastAPI
│   ├── app/
│   │   ├── api/routes/          Endpoints HTTP (health)
│   │   ├── core/                Configuración (Pydantic Settings) y logging
│   │   ├── database/            Engine, sesión y Base declarativa
│   │   ├── models/              Modelos ORM (SQLAlchemy)
│   │   ├── schemas/             DTOs (Pydantic)
│   │   ├── repositories/        Acceso a datos
│   │   ├── services/            Lógica de negocio
│   │   ├── rag/                 Módulo RAG — clases base (pendiente)
│   │   │   ├── chunker.py
│   │   │   ├── embedding_service.py
│   │   │   ├── qdrant_service.py
│   │   │   ├── indexer.py
│   │   │   ├── retriever.py
│   │   │   ├── llm_service.py
│   │   │   └── prompt_builder.py
│   │   ├── documents/           Carga/parseo de documentos — clases base (pendiente)
│   │   │   ├── pdf_loader.py
│   │   │   ├── pdf_parser.py
│   │   │   └── ocr.py
│   │   ├── utils/               Utilidades
│   │   └── main.py              Punto de entrada FastAPI + logging middleware
│   ├── alembic/                 Migraciones
│   ├── .env.example             Plantilla de variables de entorno
│   └── requirements.txt
│
├── frontend/                    Angular 20
│   ├── src/app/
│   │   ├── core/                Servicios y modelos (HealthService)
│   │   ├── features/            Vistas (home, chat, documents, catalog)
│   │   ├── layout/              Layout principal
│   │   └── shared/              Componentes/pipes/directivas compartidos
│   ├── src/environments/        apiUrl por entorno
│   └── proxy.conf.json          Proxy dev → FastAPI
│
├── scripts/
│   └── setup-qdrant.ps1         Descarga el binario de Qdrant + dashboard
│
└── qdrant-x86_64-pc-windows-msvc/   Binario y datos de Qdrant (ignorados en git)
```
