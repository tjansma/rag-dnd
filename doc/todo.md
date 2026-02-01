# TODO

## v0.2: Automation & Workflow (Current Focus)

- [x] **Refactor Project Structure**
  - [x] Create `hooks/` package and move `rag-hook.py` to `hooks/context.py` (and `query_hook.py`).
  - [x] Update `pyproject.toml` with `[project.scripts]` entry points.
- [x] **Implement Summarization Pipeline** (Client-side via Gemini CLI)
  - [x] **Transcript Extraction**: Retrieve full session history from SQLite.
  - [x] **Summarization**: Use Gemini CLI to generate high-level summaries of sessions.
  - [x] **Ingestion**: Store summaries in logbook (append).
  - [x] **CLI**: Add `llm summarize <session_id>` command.
- [ ] **Implement Auto-Transcription Hook (`rag-logger`)**
  - [ ] **Research**: Create dummy logger to inspect `AfterAgent` JSON payload.
  - [ ] **Develop `hooks/logger.py`**:
    - [ ] Read JSON from stdin.
    - [ ] Extract user `prompt` and AI `response` (filtering out thoughts/tools).
    - [ ] Append to `data/session_transcript.txt` with timestamp.
  - [ ] **Configuration**: Update `settings.json` to trigger on `AfterAgent`.

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

### 2. Feature: Hybrid Search (BM25 + Semantic)

- **Goal**: Improve retrieval of specific terms (names, locations) that semantic search misses.
- **Strategy**:
  - Enable FTS5 full-text search in SQLite on the chunks table.
  - Implement Reciprocal Rank Fusion (RRF) to combine Vector + Keyword scores.
  - Update `rag.query` to use this hybrid retriever.

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
