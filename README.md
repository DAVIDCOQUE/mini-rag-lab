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
| Qdrant | binario incluido en `qdrant-x86_64-pc-windows-msvc/` |
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

```bash
cd qdrant-x86_64-pc-windows-msvc
qdrant.exe
```

- REST API: http://localhost:6333
- Dashboard: http://localhost:6333/dashboard

> Aún no se usa desde el backend; se integrará en clases futuras.

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
└── qdrant-x86_64-pc-windows-msvc/   Binario y datos de Qdrant (ignorados en git)
```
