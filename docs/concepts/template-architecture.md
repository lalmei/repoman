# Template architecture

This page describes the architecture of the optional FastAPI and RAG parts of the repoman template. When you generate a project with `fastapi_enabled` or `rag_enabled`, the template produces the structure and behavior outlined below. Template source lives under `src/repoman/main_template/`; generated code ends up under `src/<package>/` in the created project.

## FastAPI template

When `fastapi_enabled` is true, the template generates an `app/` package with a standard FastAPI setup: ASGI entry point, lifespan-managed state, a root router with configurable prefix, and optional health/ready and RAG controllers.

### Entry point and lifespan

- **Entry:** The app is created by `get_application()` in `app/asgi.py`. It builds a `FastAPI` instance with title, description, version, and debug/docs settings from config, and registers the root router and a custom HTTP exception handler.
- **Lifespan:** A single lifespan context manager runs on startup and shutdown. On startup it:
  - Loads `Config()` and stores it on `app.state.config`
  - Initializes the shared `AiohttpClient` from `FastAPIConfig`
  - If RAG is enabled, builds `RAGContainer(config.rag_config)` and `RAGService(container)` and stores the service on `app.state.rag_service`
  On shutdown it closes the AiohttpClient.

Template file: `src/repoman/main_template/src/{{ python_package_import_name }}/app/asgi.py.jinja`.

### Config

- **Config:** The main `Config` (in the package `config` module) holds `fastapi_config: FastAPIConfig` and, when RAG is enabled, `rag_config: RAGConfig`.
- **FastAPIConfig:** Supplies `api_prefix`, `docs_url`, `debug`, and other FastAPI-related settings (e.g. from environment or config files).

Template files: `app/` uses `config/main_config.py.jinja` and `config/fastapi_config.py.jinja`.

### Router and controllers

- **Router:** The root API router is built in `app/router.py`. It applies the API prefix from config and mounts:
  - When `include_health_endpoints` is true: ready and health_check controllers (tags: ready, health check)
  - When RAG is enabled: the RAG controller router at prefix `/rag` (tags: rag)
- **Controllers:** Health and ready live in `app/controllers/health_check.py` and `app/controllers/ready.py`. RAG routes live in `app/controllers/rag/`: `GET /rag/health`, `POST /rag/query`, `POST /rag/ingest`. The RAG controller uses a dependency `get_rag_service(request)` that reads `request.app.state.rag_service`.

Template files: `app/router.py.jinja`, `app/controllers/health_check.py.jinja`, `app/controllers/ready.py.jinja`, `app/controllers/rag/routes.py.jinja`.

### State and utilities

- **State:** `app.state.config` and, when RAG is enabled, `app.state.rag_service` are set in lifespan and used by controllers and dependencies.
- **Exceptions and views:** Custom `HTTPException` and handler live in `app/exceptions/`; error and ready views in `app/views/`.
- **Utils:** `app/utils/aiohttp_client.py` provides a shared AiohttpClient used by the app (created in lifespan, closed on shutdown).

Template files: `app/state/app_state.py.jinja`, `app/exceptions/http.py.jinja`, `app/views/error.py.jinja`, `app/views/ready.py.jinja`, `app/utils/aiohttp_client.py.jinja`.

## RAG template

When `rag_enabled` is true, the template generates a `rag/` package implementing a retrieval-augmented generation (RAG) flow: ingest documents into a vector index and docstore, then answer queries by retrieving context and generating an answer with citations. The same logic is exposed via CLI (`rag ingest`, `rag query`) and, when FastAPI is enabled, via API routes under `/rag`.

### RAGService facade

`RAGService` is the single entry point used by both CLI and API:

- **query(text, filters, top_k, rerank_top_k):** Runs the full RAG pipeline: retrieve relevant chunks (with optional reranking), then generate an answer with citations. Returns a `RAGAnswer` (text, citations, query).
- **ingest(path, corpus_id):** Loads a document from path, chunks it, embeds chunks, and writes to the vector index and docstore. Returns an `IngestResult`.
- **health():** Returns a dict indicating which RAG components are configured (for `/rag/health`).

Template file: `src/repoman/main_template/src/{{ python_package_import_name }}/rag/service.py.jinja`.

### RAGContainer (wiring)

`RAGContainer` builds concrete implementations from `RAGConfig` and exposes them as the ports used by the pipelines. It lazily constructs:

- **Embedder:** Sentence-transformers embedder (port: `EmbedderPort`)
- **Vector index:** FAISS (port: `VectorIndexPort`)
- **Docstore:** SQLite-backed docstore (port: `DocstorePort`)
- **Reranker:** Sentence-transformers reranker (port: `RerankerPort`)
- **LLM:** Stub LLM (port: `LLMPort`)
- **Prompt builder:** Builds the RAG answer prompt from query and context

Template file: `rag/wiring/container.py.jinja`. Config is defined in `config/rag_config.py.jinja` and re-exported for RAG in `rag/infra/config.py.jinja`.

### Pipelines

The RAG core is organized into three pipelines:

- **Ingest pipeline** (`rag/core/pipeline/ingest.py`): Load document → chunk → embed → add to vector index and docstore.
- **Retrieve pipeline** (`rag/core/pipeline/retrieve.py`): Embed query → search vector index → optionally rerank → fetch full chunks from docstore.
- **Generate pipeline** (`rag/core/pipeline/generate.py`): Build prompt from query + context → call LLM → parse answer and citations.

The top-level `run_rag()` in `rag/core/pipeline/rag.py` composes retrieve then generate to produce a `RAGAnswer`.

Template files: `rag/core/pipeline/ingest.py.jinja`, `rag/core/pipeline/retrieve.py.jinja`, `rag/core/pipeline/generate.py.jinja`, `rag/core/pipeline/rag.py.jinja`.

### Ports and adapters

The RAG logic depends on abstract **ports** (interfaces) in `rag/core/ports/`:

- `EmbedderPort`, `VectorIndexPort`, `DocstorePort`, `RerankerPort`, `LLMPort`

**Adapters** in `rag/adapters/` provide concrete implementations:

- Sentence-transformers for embedding and reranking
- FAISS for the vector index
- SQLite for the docstore
- A stub LLM for generation (replace with a real LLM in your project)

Template files: `rag/core/ports/*.jinja`, `rag/adapters/*.jinja`.

### CLI and API

- **CLI:** When the project has a CLI (`python_package_command_line_name`), the template adds `rag` subcommands: `rag ingest` and `rag query`. They call `_get_rag_service()` which builds `Config`, `RAGContainer(config.rag_config)`, and `RAGService(container)`.
- **API:** When FastAPI is enabled, the RAG controller mounts routes under `/rag`: `GET /rag/health`, `POST /rag/query`, `POST /rag/ingest`. The controller uses the `RAGService` from `app.state.rag_service` (set in lifespan).

Template files: `cli/commands/rag/__init__.py.jinja`, `cli/commands/rag/ingest.py`, `cli/commands/rag/query.py`, `app/controllers/rag/routes.py.jinja`.

### RAG config

`RAGConfig` (in `config/rag_config.py`) holds RAG-specific settings: embedder model, reranker model, docstore path, chunk size/overlap, and flags such as `ingest_enabled`. It is loaded via pydantic-settings (env prefix `RAG_`, optional `rag_config.json`).

Template file: `config/rag_config.py.jinja`.

### RAG architecture (ASCII)

The following diagram is shared with the generated project README and instantiated docs. It shows how FastAPI/Typer, RAGService, and the three pipelines (Ingest, Retrieve, Generate) sit above the ports and adapters.

```
                    +------------------+
                    |  FastAPI / Typer |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    |   RAGService     |
                    +--------+---------+
                             |
         +-------------------+-------------------+
         v                   v                   v
  +-------------+   +---------------+   +----------------+
  |  Ingest     |   |  Retrieve     |   |  Generate      |
  |  Pipeline   |   |  Pipeline     |   |  Pipeline      |
  +------+------+   +-------+-------+   +--------+-------+
         |                  |                    |
         v                  v                    v
  +-------------+   +---------------+   +----------------+
  | Chunker     |   | Embedder      |   | LLM (stub)     |
  | Embedder    |   | VectorIndex   |   | PromptBuilder  |
  | VectorIndex |   | Reranker     |   +----------------+
  | Docstore    |   | Docstore      |
  +-------------+   +---------------+
         |                  |
         v                  v
  +-------------+   +---------------+   +----------------+
  | FAISS       |   | SQLite        |   | sentence-      |
  | (adapter)   |   | (adapter)     |   | transformers   |
  +-------------+   +---------------+   +----------------+
```

For conditional structure (when FastAPI or RAG are generated), see [Template structure](../template-structure.md).
