# TODO

## v0.2: Automation & Workflow (Current Focus)

- [ ] **Refactor Project Structure**
  - [ ] Create `hooks/` package and move `rag-hook.py` to `hooks/context.py`.
  - [ ] Update `pyproject.toml` with `[project.scripts]` entry points.
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

## Pending Tasks (Backlog)

- [x] **MCP Server**: Implement `search_logs` tool calling the API.
- [ ] **Agent Modularization**: Research Pub/Sub architecture, for adding multiple agents that can independently subscribe to game events and add context to the user's query.
- [x] **Multipart Upload**: Refactor file upload API (`/v2/document`).
- [ ] **Multipart Update**: Implement `PUT /v2/document` for updating existing files.
