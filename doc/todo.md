# TODO

## v0.1: Core RAG & Clients (Completed)

### Core RAG Logic

- [x] **Implement `ParentChildRetriever` class** (Implemented as `query` in `rag/manager.py`)
  - [x] Initialize with `Embedding` and `VectorStore` (Chroma) + `Database` (SQLite).
  - [x] **Method `search(query: str, k: int = 5)`**:
    1.  Embed input `query`.
    2.  Query `VectorStore` (ChromaDB) to get top `k` matching **child sentences**.
    3.  Extract unique `parent_ids` from the metadata of these children.
    4.  Retrieve the full **Parent Chunk** text from SQLite for these IDs.
    5.  Return the list of unique Parent texts (Full Scenes).

### Update logic

- [x] **Implement `update_document(filename: str)` in `rag/manager.py`**:
  - [x] **Check Hash**: Compare `sha256` of file on disk with `file_hash` in SQLite.
  - [x] **Cleanup Old Data**: Delete old chunks and embeddings.
  - [x] **Re-Index**: Call `store_document` logic.
  - [x] Update `Document` record in SQLite.

### Client/Server Architecture

- [x] **Implement Core REST API (`rag/server.py` -> `api/`)**
  - [x] Endpoints: `POST /rag_query`, `POST /document`, `PUT /document`, `DELETE /document`.
- [x] **Refactor Integrations to use API**
  - [x] **MCP Server**: Becomes a thin client that calls the REST API (`rag-mcp-server.py`).
  - [x] **Gemini CLI Hook**: A script that sends a generic `POST /query` to the running server (`rag-hook.py`).
  - [x] **CLI Admin Tool**: A `typer`/`click` app that sends commands to the REST API (`rag-cli.py`).

## v0.2: Automation & Workflow (Completed)

- [x] **Refactor Project Structure**
  - [x] Create `hooks/` package and move `rag-hook.py` to `hooks/context.py` (and `query_hook.py`).
  - [x] Update `pyproject.toml` with `[project.scripts]` entry points.
- [x] **Implement Summarization Pipeline** (Client-side via Gemini CLI)
  - [x] **Transcript Extraction**: Retrieve full session history from SQLite.
  - [x] **Summarization**: Use Gemini CLI to generate high-level summaries of sessions.
  - [x] **Ingestion**: Store summaries in logbook (append).
  - [x] **CLI**: Add `llm summarize <session_id>` command.
- [x] **Implement Auto-Transcription Hook (`rag-logger`)**
  - [x] **Research**: Create dummy logger to inspect `AfterAgent` JSON payload.
  - [x] **Develop `hooks/log_hook.py`**:
    - [x] Read JSON from stdin.
    - [x] Extract user `prompt` and AI `response`.
    - [x] Store via `transcribe_turn()` to SQLite.
  - [x] **Configuration**: Entry point `rag-hook-logger` in `pyproject.toml`.

## v0.2.1: Code Quality & Session Management (Completed)

- [x] **Database Session Management Refactor**
  - [x] Singleton engine in `database.py` (was: new engine per call).
  - [x] `@contextmanager get_session()` met `finally: close()`.
  - [x] `expire_on_commit=False` voor veilig gebruik na expunge.
  - [x] `_store_impl`/`_delete_impl` internal helpers met session parameter.
  - [x] `update_document` deelt één session over delete+store cyclus.
- [x] **Error Handling**
  - [x] Domain exceptions (`DocumentExistsError`, `DocumentNotFoundError`).
  - [x] Alle bare `except:` vervangen door specifieke exception types.
  - [x] `routes_v2.py`: `DatabaseError` → domain exceptions via `rag.*`.
- [x] **Code Quality Fixes**
  - [x] Mutable default arguments gefixed (`Config.load()` → `None` + body check).
  - [x] `_env_override()` helper voor correcte boolean parsing.
  - [x] `_is_writable()`: bare `except:` → `except OSError:`.
  - [x] `limit` parameter doorgegeven in `routes.py`.
  - [x] Unclosed file handles → `with open()`.
  - [x] Import shadowing in `chunker.py` opgelost.
  - [x] Dead imports/code verwijderd (`query_hook.py`).
  - [x] Hardcoded debug pad verwijderd.
  - [x] `__all__` export list in `rag/__init__.py`.
  - [x] `CampaignMetadata.load_by_*`: `expunge_all()` voor detached objecten.

## v0.3: Multi-Campaign Architecture (Completed)

- [x] **Design Status**
  - [x] Analyze project and requirements.
  - [x] Create design document: `doc/campaign_structure_design.md`.
- [x] **Server Logic**
  - [x] `Campaign` class with `create()`, `list_all()`, `from_db_by_short_name()`.
  - [x] v2 RESTful API: `POST/GET /v2/campaigns`, campaign-scoped document/query routes.
  - [x] `ensure_collection()` with own session management.
  - [x] ChromaDB-compatible collection naming (`_-_` separator).
  - [x] `CampaignMetadata` model with `short_name` validator.
- [x] **Document Model Refactor**
  - [x] Removed `Document.file_name` (redundant with `custom_filename`).
  - [x] `chunker.chunk()` accepts `source_file: Path` parameter.
  - [x] `load_document_text()` decoupled from ORM, accepts `Path`.
- [x] **Client Updates**
  - [x] `ClientConfig`: `campaign` + `collection` fields, `RAG_DND_CAMPAIGN` env var.
  - [x] `RAGClient`: v2 methods + `list_campaigns()` + `create_campaign()`.
  - [x] CLI: `--campaign` flag, lazy init, `campaign list/create` commands.
  - [x] Hooks & MCP: campaign-aware via shared `ClientConfig` (no code changes needed).
- [x] **Deferred to future version**
  - [x] Data separation: Move user data to `~/.rag_dnd/campaigns/`.
  - [ ] `PromptEngine`: Server-side system prompt rendering.

## v1.0: Enterprise Readiness (Roadmap)

### 1. Refactor: Project Structure (Completed)

- **Goal**: Professionalize the repository by moving scripts into a proper Python package structure.
- **Tasks**:
  - [x] Create `rag_dnd` or `rag` package root.
  - [x] Example structure:
    ```text
    src/rag_dnd/
      core/ (manager, models, database)
      server/ (api, routes)
      cli/ (commands)
      hooks/ (logger, context)
    ```
  - [x] Use `pyproject.toml` entry points for `rag-server`, `rag-cli`, `rag-hook`.

### 2. Feature: Multi-Query Decomposition (v1.x)

- **Goal**: Expand user queries into multiple sub-queries for broader semantic coverage.
- **Tasks**:
  - [ ] Implement HyDE or Decomposition prompt.
  - [ ] Parallelize vector searches.
  - [ ] Rerank/Deduplicate results.

### 3. Feature: Hybrid Search (BM25 + Semantic) (Completed)

- **Goal**: Improve retrieval of specific terms (names, locations) that semantic search misses.
- **Strategy**:
  - [x] **Ensemble Retriever**: Implemented custom `VectorStore` with `rank_bm25`.
  - [x] **In-Memory Index**: Builds BM25 index on startup from ChromaDB documents.
  - [x] **Search**: Implemented Reciprocal Rank Fusion (RRF) to combine Vector + Keyword scores.

### 3. Tooling: Re-indexing & Maintenance

- **Goal**: Allow regenerating the vector store without data loss when models/strategies change.
- **Tasks**:
  - Add `rag-cli reindex` command.
  - Should iterate over all `Document` entries, re-read their source file (or stored BLOB), and re-run chunking + embedding.
  - Add versioning to embeddings to detect outdated vectors.

### 4. Feature: Metadata Filtering

- **Goal**: Enable scoped searches (e.g., "What happened in Session 3?").
- **Tasks**:
  - Extract metadata (Session #, Date, Author) during ingestion.
  - Store in ChromaDB metadata fields.
  - Update API `POST /query` to accept a `filter` dictionary.

### 5. Observability: Health Endpoint

- **Goal**: Provide runtime status.
- **Tasks**:
  - Add `GET /health` endpoint.
  - Returns: DB connectivity, Vector store size, Model device (CUDA/CPU).

### 6. Feature: Advanced Content Support

- **Goal**: Support more diverse input formats.
- **Tasks**:
  - **Importers**: Add support for PDF (via `pypdf` or `pymupdf`) and other Markdown dialects.
  - **Multimodality**: Extract images/tables from PDFs. (Future: Audio transcription ingest).
  - **Character Bibles**: Specific logic to index comprehensive character background docs ("Bibles") distinct from session logs.

### 7. Feature: Structured D&D Data (RDBMS)

- **Goal**: Integrate structured game mechanisc data for context enrichment.
- **Tasks**:
  - Models for: Ability Scores, Skills, Inventory, Spells.
  - **entity-linking**: Scan user prompt for character names -> fetch their structured sheet -> inject into context.
  - Hybrid retrieval: "What spells does X have?" -> query RDBMS + Vector Store.

## Backlog (v2.0+)

- [ ] **Agent Modularization**: Research Pub/Sub architecture.
- [ ] **Multi-Agent Simulation**: Independent agents subscribing to the transcript stream.

## Technical Debt (Remaining)

- [x] **`content_database` HACK in `config.py`**: Intermediate key met `del` — fragiel bij refactoring. Fix bij v0.3.
- [x] **`Collection.campaign_id`**: Non-nullable FK zonder campaign context — fix bij v0.3 multi-campaign.
- [x] **CLI Config Validatie**: De CLI geeft direct een foutmelding als `campaign` ontbreekt in config/env, blokkeert commando's als `rag-cli campaign list` en `create`. Fixen dat dit pas gecheckt wordt als de specifieke actie dit vereist.
