# TODO

## Core RAG Logic (Implemented)

- [x] **Implement `ParentChildRetriever` class** (Implemented as `query` in `rag/manager.py`)
  - [x] Initialize with `Embedding` and `VectorStore` (Chroma) + `Database` (SQLite).
  - [x] **Method `search(query: str, k: int = 5)`**:
    1.  Embed input `query`.
    2.  Query `VectorStore` (ChromaDB) to get top `k` matching **child sentences**.
    3.  Extract unique `parent_ids` from the metadata of these children.
    4.  Retrieve the full **Parent Chunk** text from SQLite for these IDs.
    5.  Return the list of unique Parent texts (Full Scenes).

## Update logic (Implemented via API)

- [x] **Implement `update_document(filename: str)` in `rag/manager.py`**:
  - [x] **Check Hash**: Compare `sha256` of file on disk with `file_hash` in SQLite.
    - If match: Do nothing (idempotent).
    - If mismatch: Proceed to update.
  - [x] **Cleanup Old Data**:
    - Query SQLite for all `Chunk`s associated with the `Document`.
    - Extract `chunk_id`s.
    - Delete from ChromaDB (`collection.delete(where={"chunk_id": ...})`).
    - Delete `Chunk`s and `Sentences` from SQLite.
  - [x] **Re-Index**: Call `store_document` logic (Chunk -> Embed -> Store) for the new content.
  - [x] Update `Document` record in SQLite with new hash.

## Client/Server Architecture (In Progress)

**Reasoning:** To handle concurrency issues between long-running processes (MCP Server) and ephemeral ones (CLI Hooks, Admin CLI) accessing the same SQLite/ChromaDB files, we will move to a client-server model.

- [x] **Implement Core REST API (`rag/server.py` -> `api/`)**
  - [x] Use `FastAPI` to create a lightweight server.
  - [x] **Endpoints**:
    - [x] `POST /rag_query`: Accepts query text, returns relevant chunks.
    - [x] `POST /document`: Accepts file path/content, triggers indexing.
    - [x] `PUT /document`: Triggers update/re-indexing.
    - [x] `DELETE /document`: Removes document and embeddings.
  - [x] Manage the _single_ connection to ChromaDB and SQLite here.

- [x] **Refactor Integrations to use API**
  - [x] **MCP Server**: Becomes a thin client that calls the REST API (`rag-mcp-server.py`).
  - [x] **Gemini CLI Hook**: A script that sends a generic `POST /query` to the running server (`rag-hook.py`).
  - [x] **CLI Admin Tool**: A `typer`/`click` app that sends commands to the REST API (`rag-cli.py`).

## Pending Tasks

- [x] **CLI Interface**: `add`, `remove`, `update`, `search` commands using `typer`.
- [x] **MCP Server**: Implement `search_logs` tool calling the API.
- [x] **Gemini Hook**: Implement prompt injection logic.

## Legacy / Direct Library Tasks (On Hold/Deprecated by Server plan)

- [x] _Create Entrypoint Script (Hook)_ (Superseded by API client approach)
- [x] _Create `server.py` MCP_ (Superseded by API client approach)
- [x] _CLI management interface_ (Superseded by API client approach)
