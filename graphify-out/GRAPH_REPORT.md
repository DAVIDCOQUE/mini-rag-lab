# Graph Report - mini-rag-lab  (2026-10-07)

## Corpus Check
- 96 files · ~22,725 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 718 nodes · 1095 edges · 50 communities (41 shown, 9 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 113 edges (avg confidence: 0.66)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fa55ecfe`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- PDF Parsing & Chunking
- Chat & Search Client Services
- Documents Feature & Models
- Angular Build Tooling Deps
- Angular Build Targets Config
- Document Persistence Layer
- Project Docs & UI Templates
- Chat, Logging & LLM Services
- Angular Runtime Dependencies
- Documents API & Schemas
- App Shell & Main Layout
- Angular Workspace Config
- Qdrant Vector Store Service
- Health Check Services
- Chat Component Interactions
- Semantic Search Endpoint
- App Settings & Config
- Cross-Encoder Reranker
- Ollama Embedding Service
- Indexing Orchestrator
- Retriever Pipeline
- Retrieval Evaluation Script
- Search Component
- Documents Table Migration
- OCR Stub
- PDF Loader Stub
- LLM Service Stub
- Qdrant Point Search
- Health Response Schema
- Package Init Marker
- Package Init Marker
- docker-entrypoint.sh

## God Nodes (most connected - your core abstractions)
1. `Document` - 22 edges
2. `DocumentsComponent` - 20 edges
3. `PdfParser` - 17 edges
4. `DocumentProcessingService` - 16 edges
5. `Chunker` - 15 edges
6. `QdrantService` - 15 edges
7. `UiPreferencesService` - 14 edges
8. `PromptsComponent` - 14 edges
9. `EmbeddingService` - 12 edges
10. `EmptyDocumentError` - 12 edges

## Surprising Connections (you probably didn't know these)
- `Backend (FastAPI) setup guide` --semantically_similar_to--> `Mini RAG Lab (README)`  [INFERRED] [semantically similar]
  backend/README.md → README.md
- `Ambient service status in the rail` --shares_data_with--> `Contrato del health check (database, qdrant, ollama)`  [INFERRED]
  frontend/src/app/layout/main-layout.component.html → README.md
- `Home overview template (hero + health status + path cards)` --shares_data_with--> `Contrato del health check (database, qdrant, ollama)`  [INFERRED]
  frontend/src/app/features/home/home.component.html → README.md
- `Frontend Angular CLI guide` --conceptually_related_to--> `Proxy de desarrollo Angular → FastAPI (mismo origen, sin CORS)`  [INFERRED]
  frontend/README.md → README.md
- `_resolve_filenames()` --calls--> `get_document()`  [INFERRED]
  backend/app/api/routes/chat.py → backend/app/api/routes/documents.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Stack de infraestructura verificado por /health (PostgreSQL, Qdrant, Ollama)** — readme_health_check_contract, readme_postgres_hosting_open, readme_qdrant_setup_script, readme_bge_m3_embeddings, readme_qwen25_chat_model [EXTRACTED 1.00]
- **Flujo PDF → chunks → embeddings → Qdrant → búsqueda reordenada** — readme_api_endpoints, readme_rag_pipeline, readme_bge_m3_embeddings, readme_cross_encoder_reranking, readme_qdrant_setup_script [EXTRACTED 1.00]
- **Arranque del repo tras clonar (artefactos fuera de git que hay que recrear)** — readme_qdrant_setup_script, readme_postgres_hosting_open, readme_ai_skills_setup, readme_graphify_knowledge_graph [INFERRED 0.85]
- **Angular feature templates sharing one design system (surface/eyebrow/enter/copy())** — frontend_src_app_features_home_home_component_home_template, frontend_src_app_features_chat_chat_component_chat_template, frontend_src_app_features_documents_documents_component_documents_template, frontend_src_app_features_search_search_component_search_template, frontend_src_app_layout_main_layout_component_main_layout_template [EXTRACTED 1.00]

## Communities (50 total, 9 thin omitted)

### Community 0 - "PDF Parsing & Chunking"
Cohesion: 0.07
Nodes (39): Chunker, Divide el texto en chunks respetando frases (RecursiveCharacterTextSplitter)., Trocea cada pagina por separado y conserva su numero en metadata['page'] (1-inde, Quita headers/footers: lineas repetidas en la mayoria de paginas, conservando la, Une los saltos de linea de line-wrap (conservando parrafos) para no cortar frase, Indexer, UUID, Orquesta el indexado: chunks -> embeddings -> almacenamiento en Qdrant. (+31 more)

### Community 1 - "Chat & Search Client Services"
Cohesion: 0.18
Nodes (5): MainLayoutComponent, NavItem, ServiceState, toServiceState(), Component

### Community 2 - "Documents Feature & Models"
Cohesion: 0.10
Nodes (12): ChunkResult, DocumentItem, DocumentStatus, DocumentUpdate, IndexedChunks, IndexResult, ProcessingResult, DocumentService (+4 more)

### Community 3 - "Angular Build Tooling Deps"
Cohesion: 0.05
Nodes (41): chat(), ScoredPoint, Session, RAG conversacional. El router decide si la pregunta necesita el corpus o no., Nombre original de cada chunk recuperado, cacheado por documento para no repetir, _resolve_filenames(), health(), Estado del servicio verificando la conectividad real de PostgreSQL, Qdrant y Oll (+33 more)

### Community 4 - "Angular Build Targets Config"
Cohesion: 0.05
Nodes (36): @angular/build, @angular/cli, @angular/compiler-cli, devDependencies, @angular/build, @angular/cli, @angular/compiler-cli, jasmine-core (+28 more)

### Community 5 - "Document Persistence Layer"
Cohesion: 0.06
Nodes (37): build, extract-i18n, serve, test, builder, configurations, defaultConfiguration, options (+29 more)

### Community 6 - "Project Docs & UI Templates"
Cohesion: 0.07
Nodes (38): Document, Documento subido por el usuario. En esta fase solo se gestiona el archivo, sin p, ScoredPoint, UUID, QdrantService, Gestiona la conexion y las operaciones contra la base vectorial Qdrant., Crea la coleccion si no existe (vectores de EMBEDDING_DIM, distancia coseno)., Inserta/actualiza puntos. Cada item: {id, vector, payload}. (+30 more)

### Community 8 - "Angular Runtime Dependencies"
Cohesion: 0.08
Nodes (25): @angular/animations, @angular/cdk, @angular/common, @angular/compiler, @angular/core, @angular/forms, @angular/material, @angular/platform-browser (+17 more)

### Community 9 - "Documents API & Schemas"
Cohesion: 0.15
Nodes (22): create_document(), delete_document(), get_document(), get_indexed_chunks(), index_document(), list_documents(), process_document(), DocumentUpdate (+14 more)

### Community 10 - "App Shell & Main Layout"
Cohesion: 0.10
Nodes (35): Alembic migration workflow, Backend (FastAPI) setup guide, Backend pinned dependencies, Frontend Angular CLI guide, App root template (router-outlet only), Chat studio template (thread + composer + inspector), copy() signal-based i18n pattern, Failure shown as a system state with a retry exit (+27 more)

### Community 11 - "Angular Workspace Config"
Cohesion: 0.08
Nodes (42): activate_default_prompt(), activate_prompt(), create_prompt(), delete_prompt(), get_default_prompt(), get_prompt(), list_prompts(), DefaultPrompt (+34 more)

### Community 12 - "Qdrant Vector Store Service"
Cohesion: 0.08
Nodes (19): ChatMessage, ChatRole, DefaultPrompt, PromptTemplate, PromptTemplatePayload, SearchResponse, SearchResultItem, SearchRoute (+11 more)

### Community 13 - "Health Check Services"
Cohesion: 0.13
Nodes (14): cli, analytics, prefix, projectType, root, schematics, sourceRoot, newProjectRoot (+6 more)

### Community 14 - "Chat Component Interactions"
Cohesion: 0.19
Nodes (16): Base, Base declarativa para todos los modelos ORM. Alembic la usa como metadata objeti, PromptTemplate, Variante del prompt de sistema creada desde la UI.      El prompt por defecto NO, create(), deactivate_all(), delete(), get_active() (+8 more)

### Community 15 - "Semantic Search Endpoint"
Cohesion: 0.20
Nodes (4): Injectable, UiLocale, UiPreferencesService, UiTheme

### Community 16 - "App Settings & Config"
Cohesion: 0.29
Nodes (6): get_settings(), Configuracion central de la app. Todos los valores provienen de variables de ent, URL de conexion SQLAlchemy construida a partir de las piezas POSTGRES_*., Instancia unica de settings reutilizada en toda la app., Settings, BaseSettings

### Community 17 - "Cross-Encoder Reranker"
Cohesion: 0.11
Nodes (13): Devuelve un puntaje de relevancia por documento, en el mismo orden de entrada., Reordena candidatos con un cross-encoder (lee pregunta + chunk juntos)., Reranker, ScoredPoint, Recupera los fragmentos mas relevantes para una consulta del usuario.      Dos e, Embebe la consulta y devuelve los chunks mas relevantes.          Con vector se, Retriever, main() (+5 more)

### Community 18 - "Ollama Embedding Service"
Cohesion: 0.10
Nodes (22): EmbeddingService, Genera embeddings a partir de texto usando la API HTTP de Ollama (/api/embed)., Devuelve un vector por cada texto (en el mismo orden)., Embedding de una sola consulta., _cosine(), Enum, str, QueryRouter (+14 more)

### Community 19 - "Indexing Orchestrator"
Cohesion: 0.33
Nodes (4): App, appConfig, routes, Component

### Community 22 - "Search Component"
Cohesion: 0.50
Nodes (3): get_db(), Session, Dependencia FastAPI: entrega una sesion por request y la cierra al terminar.

### Community 25 - "Documents Table Migration"
Cohesion: 0.09
Nodes (23): OCR, Extrae texto de una imagen mediante EasyOCR.      Unica responsabilidad: recibir, Descarga y carga los modelos sin procesar ninguna imagen., Recibe una imagen (array HxWxC) y devuelve el texto detectado, unido por saltos, Deja el OCR listo al arrancar, no en el primer documento escaneado.      Los mod, warm_up(), PdfParser, Path (+15 more)

### Community 27 - "PDF Loader Stub"
Cohesion: 0.11
Nodes (20): generate(), LLMError, Exception, No fue posible generar una respuesta (Ollama caido o modelo ausente)., Envia el prompt a Ollama (/api/generate) y devuelve el texto generado., build_prompt(), build_simple_prompt(), Prompt sin contexto recuperado, para los caminos que no consultan la base. (+12 more)

### Community 28 - "LLM Service Stub"
Cohesion: 0.43
Nodes (4): HealthResponse, HealthService, Injectable, ConnectionState

## Knowledge Gaps
- **84 isolated node(s):** `docker-entrypoint.sh script`, `$schema`, `version`, `newProjectRoot`, `projectType` (+79 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Document` connect `Project Docs & UI Templates` to `PDF Parsing & Chunking`, `Chat Component Interactions`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `QdrantService` connect `Project Docs & UI Templates` to `PDF Parsing & Chunking`, `Cross-Encoder Reranker`, `Ollama Embedding Service`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Why does `PdfParser` connect `Documents Table Migration` to `PDF Parsing & Chunking`, `Angular Build Tooling Deps`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `Document` (e.g. with `Base` and `DocumentProcessingService`) actually correct?**
  _`Document` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `PdfParser` (e.g. with `OCR` and `DocumentProcessingService`) actually correct?**
  _`PdfParser` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `DocumentProcessingService` (e.g. with `PdfParser` and `Document`) actually correct?**
  _`DocumentProcessingService` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `Chunker` (e.g. with `DocumentProcessingService` and `.__init__()`) actually correct?**
  _`Chunker` has 8 INFERRED edges - model-reasoned connections that need verification._