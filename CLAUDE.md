# Mini RAG Lab

Laboratorio de aprendizaje de RAG. Backend FastAPI + PostgreSQL + Qdrant + Ollama,
frontend Angular 20. Las reglas generales de desarrollo están en el CLAUDE.md global;
aquí solo va lo propio de este repo.

## Configuración

Todo sale de `backend/app/core/config.py` vía `.env`. Hay dos clases de ajuste y
conviene no confundirlas.

**Acordados por el proyecto.** Cambiarlos afecta a todos: hay que hablarlo antes.

| Ajuste | Valor |
|---|---|
| Modelo de embeddings | `bge-m3` (1024 dimensiones) |
| Reranker | `jinaai/jina-reranker-v2-base-multilingual` (FastEmbed), 20 candidatos |
| Colección Qdrant | `documents` |
| Chunking | 1000 caracteres, 200 de solape |
| Prefijo de API | `/api` (`/health` va en la raíz) |

El modelo de embeddings y sus dimensiones son los más rígidos: cambiarlos invalida
la colección entera y obliga a reindexar.

**Locales de cada máquina.** No documentar aquí su valor: cada quien corre el modelo
de Ollama que tiene descargado y anotarlo provoca ediciones cruzadas de este archivo.

| Ajuste | Cómo consultar el que está activo |
|---|---|
| `LLM_MODEL` (modelo de chat) | `python -c "from app.core.config import settings; print(settings.LLM_MODEL)"` desde `backend/` |
| Modelos disponibles en la máquina | `ollama list` |

Antes de dar por hecho un modelo, comprobarlo: pedirle a Ollama uno que no está
descargado devuelve **404**, no un error legible.

## Estado del código

Implementado: `chunker`, `pdf_parser` (PyMuPDF), `embedding_service` (Ollama `/api/embed`),
`qdrant_service`, `indexer`, `retriever`, `reranker`, `llm_service`, `prompt_builder`,
y las rutas `health`, `chat`, `search`, `documents`, `prompts`.

Esqueleto pendiente — no tratarlos como código roto: `documents/pdf_loader.py`,
`documents/ocr.py`.

## Prompts del sistema

El prompt por defecto vive en `rag/prompt_builder.py` (`SYSTEM_PROMPT_TEMPLATE`),
versionado en git. Las variantes que se crean desde la UI viven en la tabla
`prompt_templates` y se identifican por `code`. Reglas del diseño:

- Sin variante activa —o al borrar la activa— el sistema cae al prompt del repositorio.
  Nunca hay un estado sin prompt, y `code = "default"` está reservado.
- Las variantes escriben `{no_answer}` en lugar de copiar la frase de fallback:
  `render_system_prompt()` la sustituye al construir el prompt. Así cambiar
  `NO_ANSWER_MESSAGE` no deja prompts guardados instruyendo la frase antigua.
- `/chat` usa la variante activa; `/search` acepta `prompt_code` para probar otra en
  una consulta suelta sin tocar la que el sistema tiene en uso.

`/search` con `generate: true` devuelve además la respuesta del LLM y `timings` con el
coste de cada etapa por separado. La recuperación domina el gasto (el cross-encoder
sobre 20 candidatos en CPU), no la generación.

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
alembic upgrade head          # tras un pull: la 0002 crea prompt_templates

# frontend (desde frontend/)
npm start

# qdrant (desde la raíz, una sola vez)
.\scripts\setup-qdrant.ps1
```
