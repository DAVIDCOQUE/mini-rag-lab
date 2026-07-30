# Mini RAG Lab

Laboratorio de aprendizaje de RAG. Backend FastAPI + PostgreSQL + Qdrant + Ollama,
frontend Angular 20. Las reglas generales de desarrollo están en el CLAUDE.md global;
aquí solo va lo propio de este repo.

## Configuración real (no asumir otros valores)

Todo sale de `backend/app/core/config.py` vía `.env`:

| Ajuste | Valor |
|---|---|
| Modelo de chat | `qwen2.5:7b` |
| Modelo de embeddings | `bge-m3` (1024 dimensiones) |
| Reranker | `jinaai/jina-reranker-v2-base-multilingual` (FastEmbed), 20 candidatos |
| Colección Qdrant | `documents` |
| Chunking | 1000 caracteres, 200 de solape |
| Prefijo de API | `/api` (`/health` va en la raíz) |

## Estado del código

Implementado: `chunker`, `pdf_parser` (PyMuPDF), `embedding_service` (Ollama `/api/embed`),
`qdrant_service`, `indexer`, `retriever`, `reranker`, y las rutas `health`, `chat`, `search`, `documents`.

Esqueleto pendiente — no tratarlos como código roto: `rag/llm_service.py`,
`rag/prompt_builder.py`, `documents/pdf_loader.py`, `documents/ocr.py`.

## Skills disponibles en este repo

Están en `.agents/skills/` (con junctions en `.claude/skills/`) y versionadas en
`skills-lock.json`. Usar la que corresponda al dominio antes de improvisar:

| Tarea | Skill |
|---|---|
| Rutas, dependencias, Pydantic, SSE/streaming en FastAPI | `fastapi` |
| Resultados de búsqueda malos, medir recall@k, híbrida, reranking, golden set | `qdrant-search-quality` |
| Loaders, splitters, embeddings, vector stores de LangChain | `langchain-rag` |
| Estado reactivo en Angular: `signal()`, `computed()`, `linkedSignal()`, `effect()` | `angular-signals` |
| Fundamentos de interfaz y movimiento (springs, interrumpibilidad, materiales) | `apple-design` |
| Auditar el movimiento existente y planificar mejoras | `improve-animations` |
| Revisar animaciones contra estándares y dar veredicto | `review-animations` |
| Prototipar una interacción antes de implementarla | `prototype` |
| Elegir librería de UI | `pick-ui-library` |

## Grafo de conocimiento

Existe `graphify-out/graph.json` (529 nodos, 737 aristas). Para preguntas de arquitectura,
"qué usa qué" o "dónde vive esto", consultarlo primero con `graphify query "<pregunta>"`
antes de rastrear con Grep/Read: es más barato y ya está construido. Leer archivos solo
para el detalle exacto que el grafo ya localizó.

Reconstruir con `graphify update .` (solo código: determinista, sin coste de tokens).
`.graphifyignore` excluye `.agents/` y `.claude/`; no quitar esa exclusión: la prosa de las
skills gasta tokens de extracción semántica e inventa comunidades ajenas al proyecto.

## Comandos

```bash
# backend (desde backend/)
uvicorn app.main:app --reload --no-access-log
alembic upgrade head

# frontend (desde frontend/)
npm start

# qdrant (desde la raíz, una sola vez)
.\scripts\setup-qdrant.ps1
```
