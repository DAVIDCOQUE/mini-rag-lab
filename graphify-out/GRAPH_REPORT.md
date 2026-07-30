# Graph Report - .  (2026-07-30)

## Corpus Check
- Corpus is ~13,529 words - fits in a single context window. You may not need a graph.

## Summary
- 535 nodes · 753 edges · 48 communities (40 shown, 8 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 75 edges (avg confidence: 0.65)
- Token cost: 44,843 input · 0 output

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
- Prompt Builder Stub
- Qdrant Point Search
- Health Response Schema
- Package Init Marker

## God Nodes (most connected - your core abstractions)
1. `Document` - 22 edges
2. `DocumentsComponent` - 20 edges
3. `DocumentProcessingService` - 16 edges
4. `QdrantService` - 15 edges
5. `UiPreferencesService` - 13 edges
6. `Chunker` - 12 edges
7. `EmptyDocumentError` - 12 edges
8. `IndexingError` - 12 edges
9. `DocumentItem` - 12 edges
10. `Indexer` - 11 edges

## Surprising Connections (you probably didn't know these)
- `Backend (FastAPI) setup guide` --semantically_similar_to--> `Mini RAG Lab (README)`  [INFERRED] [semantically similar]
  backend/README.md → README.md
- `Ambient service status in the rail` --shares_data_with--> `Contrato del health check (database, qdrant, ollama)`  [INFERRED]
  frontend/src/app/layout/main-layout.component.html → README.md
- `Home overview template (hero + health status + path cards)` --shares_data_with--> `Contrato del health check (database, qdrant, ollama)`  [INFERRED]
  frontend/src/app/features/home/home.component.html → README.md
- `Frontend Angular CLI guide` --conceptually_related_to--> `Proxy de desarrollo Angular → FastAPI (mismo origen, sin CORS)`  [INFERRED]
  frontend/README.md → README.md
- `DocumentProcessingService` --uses--> `Document`  [INFERRED]
  backend/app/services/document_processing_service.py → backend/app/models/document.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Stack de infraestructura verificado por /health (PostgreSQL, Qdrant, Ollama)** — readme_health_check_contract, readme_postgres_hosting_open, readme_qdrant_setup_script, readme_bge_m3_embeddings, readme_qwen25_chat_model [EXTRACTED 1.00]
- **Flujo PDF → chunks → embeddings → Qdrant → búsqueda reordenada** — readme_api_endpoints, readme_rag_pipeline, readme_bge_m3_embeddings, readme_cross_encoder_reranking, readme_qdrant_setup_script [EXTRACTED 1.00]
- **Arranque del repo tras clonar (artefactos fuera de git que hay que recrear)** — readme_qdrant_setup_script, readme_postgres_hosting_open, readme_ai_skills_setup, readme_graphify_knowledge_graph [INFERRED 0.85]
- **Angular feature templates sharing one design system (surface/eyebrow/enter/copy())** — frontend_src_app_features_home_home_component_home_template, frontend_src_app_features_chat_chat_component_chat_template, frontend_src_app_features_documents_documents_component_documents_template, frontend_src_app_features_search_search_component_search_template, frontend_src_app_layout_main_layout_component_main_layout_template [EXTRACTED 1.00]

## Communities (48 total, 8 thin omitted)

### Community 0 - "PDF Parsing & Chunking"
Cohesion: 0.08
Nodes (32): PdfParser, Path, Devuelve el texto de cada pagina (indice 0 = pagina 1), normalizado a NFC., Extrae el texto de un PDF usando PyMuPDF, conservando la separacion por pagina., Chunker, Divide el texto en chunks respetando frases (RecursiveCharacterTextSplitter)., Trocea cada pagina por separado y conserva su numero en metadata['page'] (1-inde, Quita headers/footers: lineas repetidas en la mayoria de paginas, conservando la (+24 more)

### Community 1 - "Chat & Search Client Services"
Cohesion: 0.06
Nodes (19): App, appConfig, routes, Component, HealthResponse, HealthService, Injectable, Injectable (+11 more)

### Community 2 - "Documents Feature & Models"
Cohesion: 0.10
Nodes (12): ChunkResult, DocumentItem, DocumentStatus, DocumentUpdate, IndexedChunks, IndexResult, ProcessingResult, DocumentService (+4 more)

### Community 3 - "Angular Build Tooling Deps"
Cohesion: 0.06
Nodes (28): chat(), Reenvia el mensaje del usuario a Ollama y devuelve la respuesta del modelo., health(), Estado del servicio verificando la conectividad real de PostgreSQL, Qdrant y Oll, configure_logging(), Configura el logging basico en consola para toda la aplicacion., log_requests(), Registra metodo, ruta, codigo HTTP y tiempo de respuesta de cada peticion. (+20 more)

### Community 4 - "Angular Build Targets Config"
Cohesion: 0.05
Nodes (36): @angular/build, @angular/cli, @angular/compiler-cli, devDependencies, @angular/build, @angular/cli, @angular/compiler-cli, jasmine-core (+28 more)

### Community 5 - "Document Persistence Layer"
Cohesion: 0.06
Nodes (37): build, extract-i18n, serve, test, builder, configurations, defaultConfiguration, options (+29 more)

### Community 6 - "Project Docs & UI Templates"
Cohesion: 0.10
Nodes (32): Base, Base declarativa para todos los modelos ORM. Alembic la usa como metadata objeti, Document, Documento subido por el usuario. En esta fase solo se gestiona el archivo, sin p, create(), delete(), get(), list_all() (+24 more)

### Community 7 - "Chat, Logging & LLM Services"
Cohesion: 0.11
Nodes (8): ChatMessage, ChatRole, ChatApiResponse, ChatErrorKind, ChatService, Injectable, ChatComponent, Component

### Community 8 - "Angular Runtime Dependencies"
Cohesion: 0.08
Nodes (25): @angular/animations, @angular/cdk, @angular/common, @angular/compiler, @angular/core, @angular/forms, @angular/material, @angular/platform-browser (+17 more)

### Community 9 - "Documents API & Schemas"
Cohesion: 0.15
Nodes (22): create_document(), delete_document(), get_document(), get_indexed_chunks(), index_document(), list_documents(), process_document(), DocumentUpdate (+14 more)

### Community 10 - "App Shell & Main Layout"
Cohesion: 0.17
Nodes (18): App root template (router-outlet only), Chat studio template (thread + composer + inspector), copy() signal-based i18n pattern, Failure shown as a system state with a retry exit, Send and stop share one slot (affordance changes, control does not move), Chunk inspector dialogs (process result vs indexed vectors), Document status lifecycle (process → index → INDEXED inspect), Documents library template (toolbar + doc cards + dialogs) (+10 more)

### Community 11 - "Angular Workspace Config"
Cohesion: 0.23
Nodes (17): Alembic migration workflow, Backend (FastAPI) setup guide, Backend pinned dependencies, Frontend Angular CLI guide, Skills de IA versionadas y gestionadas con npx skills, Superficie HTTP de la API (/health y prefijo /api), Embeddings con bge-m3 (1024 dimensiones), Reranking con cross-encoder vía FastEmbed (+9 more)

### Community 12 - "Qdrant Vector Store Service"
Cohesion: 0.18
Nodes (7): SearchResponse, SearchResultItem, SearchService, Injectable, SearchComponent, Component, environment

### Community 13 - "Health Check Services"
Cohesion: 0.13
Nodes (14): cli, analytics, prefix, projectType, root, schematics, sourceRoot, newProjectRoot (+6 more)

### Community 14 - "Chat Component Interactions"
Cohesion: 0.19
Nodes (7): UUID, QdrantService, Gestiona la conexion y las operaciones contra la base vectorial Qdrant., Crea la coleccion si no existe (vectores de EMBEDDING_DIM, distancia coseno)., Inserta/actualiza puntos. Cada item: {id, vector, payload}., Elimina todos los vectores asociados a un documento., Devuelve todos los puntos guardados de un documento (sin el vector).

### Community 15 - "Semantic Search Endpoint"
Cohesion: 0.31
Nodes (7): Busqueda semantica: embebe la consulta y devuelve los chunks mas relevantes., search(), BaseModel, SearchRequest, SearchResponse, SearchResultItem, SearchResponse

### Community 16 - "App Settings & Config"
Cohesion: 0.29
Nodes (6): get_settings(), URL de conexion SQLAlchemy construida a partir de las piezas POSTGRES_*., Configuracion central de la app. Todos los valores provienen de variables de ent, Instancia unica de settings reutilizada en toda la app., Settings, BaseSettings

### Community 17 - "Cross-Encoder Reranker"
Cohesion: 0.25
Nodes (4): Devuelve un puntaje de relevancia por documento, en el mismo orden de entrada., Reordena candidatos con un cross-encoder (lee pregunta + chunk juntos)., Reranker, TextCrossEncoder

### Community 18 - "Ollama Embedding Service"
Cohesion: 0.33
Nodes (4): EmbeddingService, Genera embeddings a partir de texto usando la API HTTP de Ollama (/api/embed)., Devuelve un vector por cada texto (en el mismo orden)., Embedding de una sola consulta.

### Community 19 - "Indexing Orchestrator"
Cohesion: 0.33
Nodes (4): Indexer, UUID, Orquesta el indexado: chunks -> embeddings -> almacenamiento en Qdrant., Genera embeddings de los chunks y los guarda en Qdrant. Devuelve cuantos indexo.

### Community 20 - "Retriever Pipeline"
Cohesion: 0.29
Nodes (4): ScoredPoint, Recupera los fragmentos mas relevantes para una consulta del usuario.      Dos e, Embebe la consulta y devuelve los chunks mas relevantes., Retriever

### Community 21 - "Retrieval Evaluation Script"
Cohesion: 0.47
Nodes (5): main(), _matches(), _normalize(), Evalua la calidad de la recuperacion contra un set de preguntas.  Requiere Qdran, Minusculas, sin acentos y sin espacios extra, para comparar de forma robusta.

### Community 22 - "Search Component"
Cohesion: 0.50
Nodes (3): get_db(), Session, Dependencia FastAPI: entrega una sesion por request y la cierra al terminar.

## Knowledge Gaps
- **82 isolated node(s):** `$schema`, `version`, `newProjectRoot`, `projectType`, `style` (+77 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `QdrantService` connect `Chat Component Interactions` to `Indexing Orchestrator`, `Retriever Pipeline`, `Prompt Builder Stub`, `Project Docs & UI Templates`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Why does `Document` connect `Project Docs & UI Templates` to `PDF Parsing & Chunking`, `Indexing Orchestrator`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Why does `Indexer` connect `Indexing Orchestrator` to `PDF Parsing & Chunking`, `Ollama Embedding Service`, `Chat Component Interactions`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `Document` (e.g. with `Base` and `DocumentProcessingService`) actually correct?**
  _`Document` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `DocumentProcessingService` (e.g. with `PdfParser` and `Document`) actually correct?**
  _`DocumentProcessingService` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `QdrantService` (e.g. with `Indexer` and `.__init__()`) actually correct?**
  _`QdrantService` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `version`, `newProjectRoot` to the rest of the system?**
  _82 weakly-connected nodes found - possible documentation gaps or missing edges._