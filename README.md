# Mini RAG Lab

Laboratorio de aprendizaje para construir un sistema RAG paso a paso.

El circuito completo **ya funciona**: subir un PDF, extraer su texto con PyMuPDF, trocearlo
respetando frases, embeberlo con Ollama (`bge-m3`), guardarlo en Qdrant, recuperarlo con
búsqueda semántica reordenada por un cross-encoder y responder con el LLM sobre ese contexto.

Quedan dos piezas como esqueleto para clases futuras: `documents/pdf_loader.py` y
`documents/ocr.py`.

---

## Cómo se comporta la app

### Una consulta no siempre recorre el mismo camino

Antes toda pregunta pagaba la recuperación completa, aunque fuera un saludo. Ahora un
**router** clasifica primero y solo el camino institucional llega a Qdrant:

```
pregunta
   │
   ▼  embedding de la consulta (bge-m3)
 ROUTER  ─ compara ese vector con los centroides de cada camino
   │
   ├─ institutional  → Qdrant + reranker → umbral → LLM con contexto
   ├─ general        → LLM sin contexto, avisando de que es información general
   ├─ smalltalk      → LLM sin contexto, respuesta breve y cordial
   └─ off_topic      → texto fijo, sin llamar al modelo
```

El router **no usa un LLM**: compara el vector de la consulta con el promedio de unas frases
de ejemplo por camino (`rag/query_router.py`, `ROUTE_EXAMPLES`). La gracia es que ese vector
es el mismo que después necesita Qdrant, así que en el camino institucional el router no
añade ni una llamada: lo que se ahorra en los demás caminos es el **reranker**.

Tiempos medidos en caliente, en una máquina sin GPU (varían mucho con el hardware):

| Consulta | Camino | Coste |
|---|---|---|
| `Hola, soy David` | smalltalk | ~7 s |
| `¿Cuál es la mejor receta de paella?` | off_topic | ~2,5 s (sin LLM) |
| `¿Qué es un crédito académico?` | general | ~10 s |
| `¿Quién es el secretario general?` | institutional | ~18,6 s |

En esta máquina **la recuperación domina el gasto**, no la generación: el cross-encoder
reordenando 20 candidatos en CPU es el grueso de esos 18 s.

Ante la duda el router prefiere buscar (`ROUTER_SAFETY_MARGIN`): responder de memoria sobre
la institución es el peor fallo posible, porque el modelo inventa con seguridad. Se corrige
añadiendo frases al camino que corresponda; con `ROUTER_ENABLED=false` se vuelve al
comportamiento anterior de recuperar siempre.

### Cuando sí se busca, hay un corte de calidad

Recuperar no es responder. Si el mejor chunk no llega a `CHAT_MIN_SCORE`, no se llama al
modelo: se devuelve la frase de "no encontré información" sin gastar la generación. Con el
reranker activo esos scores son **logits del cross-encoder** (sin techo y con negativos), no
una similitud de 0 a 1; por eso la interfaz muestra el valor crudo (`-0.68`) y no un
porcentaje.

### El comportamiento del agente se edita sin tocar código

El prompt de sistema por defecto vive en `rag/prompt_builder.py`, versionado en git. Desde la
vista **Prompts** se crean variantes que se guardan en la tabla `prompt_templates` y se
identifican por un `code`:

- Sin variante activa —o al borrar la activa— el sistema cae al prompt del repositorio.
  Nunca hay un estado sin prompt.
- Las variantes escriben `{no_answer}` en lugar de copiar la frase de fallback; se sustituye
  al construir el prompt, de modo que cambiarla en el código actualiza todas las variantes.
- El **chat** usa la variante activa. **Explore** permite elegir otra para una consulta
  suelta, sin tocar la que el sistema tiene en uso.

### Explore enseña el flujo, no solo el resultado

La vista de búsqueda muestra, para cada consulta: el camino que eligió el router, la
respuesta generada, el coste de cada etapa por separado (enrutado / recuperación /
generación) y los chunks que se usaron como contexto, con su score real. Si el modelo no
llegó a llamarse, lo dice y explica por qué.

---

## Requisitos

| Herramienta | Versión sugerida |
|---|---|
| Python | 3.12 |
| Node.js | 20+ |
| Angular CLI | 20 |
| PostgreSQL | 16 — necesario, guarda los documentos |
| Qdrant | se descarga con `scripts\setup-qdrant.ps1` |
| Ollama | necesario, sirve los embeddings y el chat |

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

El health check **comprueba de verdad** cada servicio, no devuelve un valor fijo:
`SELECT 1` contra PostgreSQL, la lista de colecciones en Qdrant y un `GET /api/tags` en
Ollama. Cada comprobación tiene 2 s de timeout para que `/health` no se bloquee si un
servicio está caído, así que cada campo es `connected` o `disconnected`:

```json
{
  "status": "ok",
  "service": "Mini RAG Lab",
  "version": "1.0.0",
  "database": "connected",
  "qdrant": "connected",
  "ollama": "connected"
}
```

> `status` es siempre `"ok"`: solo dice que la API responde. Para saber si todo está arriba
> hay que mirar los tres campos de servicio, no `status`.

### Endpoints

`/health` se sirve en la raíz; el resto va bajo el prefijo `/api`.

| Método | Ruta | Qué hace |
|---|---|---|
| `GET` | `/health` | Estado de PostgreSQL, Qdrant y Ollama |
| `POST` | `/api/documents` | Sube un documento |
| `GET` | `/api/documents` | Lista los documentos |
| `GET` | `/api/documents/{id}` | Detalle de un documento |
| `PUT` | `/api/documents/{id}` | Actualiza sus datos administrativos |
| `DELETE` | `/api/documents/{id}` | Borra el archivo, sus vectores y el registro |
| `POST` | `/api/documents/{id}/process` | Extrae el texto del PDF y lo trocea |
| `POST` | `/api/documents/{id}/index` | Embebe los chunks y los guarda en Qdrant |
| `GET` | `/api/documents/{id}/chunks` | Devuelve los chunks ya indexados |
| `POST` | `/api/search` | Búsqueda semántica con reranking; con `generate` hace el flujo RAG completo |
| `POST` | `/api/chat` | RAG conversacional: enruta, recupera si hace falta y responde |
| `GET` | `/api/prompts` | Lista las variantes de prompt guardadas |
| `GET` | `/api/prompts/default` | Prompt del repositorio (solo lectura, de referencia) |
| `POST` | `/api/prompts` | Crea una variante |
| `PATCH` | `/api/prompts/{code}` | Edita nombre o instrucciones (el `code` no cambia) |
| `DELETE` | `/api/prompts/{code}` | Borra una variante |
| `POST` | `/api/prompts/{code}/activate` | Deja esa variante como la que usa el chat |
| `POST` | `/api/prompts/default/activate` | Vuelve al prompt del repositorio |

`POST /api/search` acepta `generate` (pasar los chunks por el LLM) y `prompt_code` (con qué
instrucciones generar). Cuando `generate` es `true` devuelve además `answer`, el `route` que
eligió el router y `timings` con el coste de cada etapa por separado.

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
Al abrir la app, el home muestra **Backend conectado** y el rail lateral refleja el estado de
PostgreSQL, Qdrant y Ollama, todo consumiendo `/health` real.

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

Dos tablas: `documents` (metadatos de cada PDF) y `prompt_templates` (las variantes de prompt
creadas desde la UI). Tras un `git pull` conviene repetir el `upgrade head`: la migración
`0002` crea la segunda.

> El backend usa SQLAlchemy con el driver `psycopg2`, así que el motor debe ser PostgreSQL;
> lo abierto es *dónde* corre, no *qué* motor es.

---

## Cómo ejecutar Ollama

```bash
# 1. Instalar desde https://ollama.com
# 2. Iniciar el servicio
ollama serve

# 3. Descargar los modelos que usa el backend
ollama pull bge-m3            # embeddings (1024 dimensiones) — acordado, no cambiar a la ligera
ollama pull <modelo-de-chat>  # el que prefieras: llama3.1:8b, qwen2.5:7b…
```

- API: http://localhost:11434

Los nombres salen de `EMBEDDING_MODEL` y `LLM_MODEL` en `backend/.env`.

**El modelo de chat es decisión de cada máquina**: cada quien corre el que tenga descargado,
así que aquí no se fija ninguno. Para ver el activo, `ollama list` o:

```bash
cd backend && python -c "from app.core.config import settings; print(settings.LLM_MODEL)"
```

> Pedirle a Ollama un modelo que no está descargado devuelve **404**, no un error legible.

El modelo de **embeddings** sí es común a todos: si lo cambias, ajusta `EMBEDDING_DIM` y
vuelve a indexar, porque la colección de Qdrant se crea con esa dimensión y no acepta
vectores de otro tamaño.

El reranking va aparte: usa un cross-encoder vía FastEmbed
(`jinaai/jina-reranker-v2-base-multilingual`), que se descarga solo la primera vez y **no**
pasa por Ollama. Se apaga con `RERANK_ENABLED=false`.

---

## Estructura del proyecto

```
mini-rag-lab/
├── backend/                     FastAPI
│   ├── app/
│   │   ├── api/routes/          Endpoints HTTP (health, chat, search, documents, prompts)
│   │   ├── core/                Configuración (Pydantic Settings) y logging
│   │   ├── database/            Engine, sesión y Base declarativa
│   │   ├── models/              Modelos ORM (SQLAlchemy)
│   │   ├── schemas/             DTOs (Pydantic)
│   │   ├── repositories/        Acceso a datos
│   │   ├── services/            Lógica de negocio
│   │   │   └── rag_service.py        orquesta el flujo: router → camino → respuesta
│   │   ├── rag/                 Módulo RAG
│   │   │   ├── chunker.py            trocea por página respetando frases
│   │   │   ├── embedding_service.py  embeddings vía Ollama /api/embed
│   │   │   ├── qdrant_service.py     colección, upsert y borrado de vectores
│   │   │   ├── indexer.py            chunks → embeddings → Qdrant
│   │   │   ├── retriever.py          recupera candidatos y reordena
│   │   │   ├── reranker.py           cross-encoder vía FastEmbed
│   │   │   ├── query_router.py       elige camino comparando con centroides
│   │   │   ├── llm_service.py        genera con Ollama /api/generate
│   │   │   └── prompt_builder.py     prompt por defecto y prompts de cada camino
│   │   ├── documents/           Carga/parseo de documentos
│   │   │   ├── pdf_parser.py         extrae texto con PyMuPDF, por página
│   │   │   ├── pdf_loader.py         (esqueleto)
│   │   │   └── ocr.py                (esqueleto)
│   │   ├── utils/               Utilidades
│   │   └── main.py              Punto de entrada FastAPI + logging middleware
│   ├── alembic/                 Migraciones
│   ├── .env.example             Plantilla de variables de entorno
│   └── requirements.txt
│
├── frontend/                    Angular 20
│   ├── src/app/
│   │   ├── core/                Modelos y servicios HTTP (health, chat, search,
│   │   │                        documents, prompts, preferencias de UI)
│   │   ├── features/            Vistas (home, chat, documents, search, prompts)
│   │   ├── layout/              Layout principal
│   │   └── shared/              Componentes/pipes/directivas compartidos
│   ├── src/environments/        apiUrl por entorno
│   └── proxy.conf.json          Proxy dev → FastAPI
│
├── scripts/
│   └── setup-qdrant.ps1         Descarga el binario de Qdrant + dashboard
│
├── .agents/skills/              Skills de IA instaladas (contenido real)
├── .claude/skills/              Skills visibles para Claude Code (junctions → .agents/skills)
├── skills-lock.json             Versiones y hashes de las skills instaladas
├── .graphifyignore              Excluye el tooling del grafo de conocimiento
├── graphify-out/                Grafo de conocimiento generado (ignorado en git)
│
└── qdrant-x86_64-pc-windows-msvc/   Binario y datos de Qdrant (ignorados en git)
```

---

## Skills de IA usadas en el proyecto

El repo versiona las skills que asisten el desarrollo, para que cualquiera que lo clone
trabaje con el mismo contexto. Se gestionan con la CLI [`npx skills`](https://skills.sh/)
y quedan registradas con su hash en `skills-lock.json`.

### Dominio del proyecto (backend, RAG, frontend)

| Skill | Fuente | Para qué |
|---|---|---|
| `fastapi` | `fastapi/fastapi` (oficial) | Convenciones de FastAPI: modelos Pydantic, dependencias, respuestas en streaming (SSE) |
| `qdrant-search-quality` | `qdrant/skills` (oficial) | Diagnosticar y mejorar la relevancia: búsqueda híbrida, reranking, medir recall@k, golden set |
| `langchain-rag` | `langchain-ai/langchain-skills` (oficial) | RAG con LangChain: loaders, `RecursiveCharacterTextSplitter`, embeddings, vector stores |
| `angular-signals` | `analogjs/angular-skills` | Estado reactivo con signals en Angular 20+: `signal()`, `computed()`, `linkedSignal()`, `effect()` |

### Interfaz y movimiento

| Skill | Fuente | Para qué |
|---|---|---|
| `apple-design` | `emilkowalski/skill` | Fundamentos de interfaz y movimiento fluido: interrumpibilidad, springs, materiales, tipografía |
| `improve-animations` | `emilkowalski/skill` | Auditar el movimiento existente y producir planes de mejora priorizados |
| `review-animations` | `emilkowalski/skill` | Revisar animaciones contra estándares y emitir un veredicto |
| `prototype` | `emilkowalski/skill` | Prototipado interactivo de interacciones antes de implementarlas |
| `pick-ui-library` | `emilkowalski/skill` | Elegir librería de UI según el caso |

```bash
# tras clonar el repo: recrea los enlaces que Claude Code lee
npx skills experimental_install

# buscar, instalar y listar
npx skills find <tema>
npx skills add <owner/repo@skill>
npx skills list

# actualizar a la última versión
npx skills update
```

El contenido real de cada skill se versiona en `.agents/skills/`. Lo que Claude Code lee es
`.claude/skills/`, que solo contiene enlaces hacia allá y está ignorado en git para no
duplicar cada archivo; de ahí el `experimental_install` tras clonar.

> Las skills corren con los permisos del agente: revisa el `SKILL.md` antes de confiar en una nueva.

---

## Grafo de conocimiento (graphify)

El repo se puede convertir en un grafo navegable de su propio código para responder preguntas
de arquitectura sin rastrear archivo por archivo. Se genera con la skill global
`graphify` (`/graphify` en Claude Code, o la CLI `graphify` del paquete `graphifyy`).

```bash
# construir o actualizar (solo código: sin LLM, sin coste de tokens)
graphify update .

# consultar
graphify query "cómo viaja un PDF desde la subida hasta Qdrant"
graphify path "Indexer" "QdrantService"
graphify explain "Retriever"
```

Salidas en `graphify-out/` (ignorado en git, se regenera):

| Archivo | Qué es |
|---|---|
| `graph.html` | Grafo interactivo, se abre en el navegador sin servidor |
| `GRAPH_REPORT.md` | Informe: comunidades, nodos más conectados, conexiones inesperadas |
| `graph.json` | Datos crudos del grafo |
| `cost.json` | Tokens consumidos por corrida |

Estado actual: **529 nodos y 737 aristas** sobre 89 archivos, agrupados en 48 comunidades.
La extracción de código es determinista (AST) y no gasta tokens; solo la prosa
(`README`s y plantillas `.html`) necesita un modelo, y queda en caché entre corridas.

`.graphifyignore` excluye `.agents/` y `.claude/`: la documentación de las skills no es
parte del proyecto, y dejarla dentro gastaba tokens e inventaba comunidades ajenas al código.
