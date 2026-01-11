# TODO

## Query logic (Implemented)
- [x] **Implement `ParentChildRetriever` class** (Implemented as `query` in `rag/manager.py`)
    - [x] Initialize with `Embedding` and `VectorStore` (Chroma) + `Database` (SQLite).
    - [x] **Method `search(query: str, k: int = 5)`**:
        1.  Embed input `query` with prefix `"query: "` (required for E5 model).
        2.  Query `VectorStore` (ChromaDB) to get top `k` matching **child sentences**.
        3.  Extract unique `parent_ids` from the metadata of these children.
        4.  Retrieve the full **Parent Chunk** text from SQLite for these IDs.
        5.  Return the list of unique Parent texts (Full Scenes).

## Update logic (re-adding of existing documents)
- [ ] **Implement `update_document(filename: str)` in `rag/manager.py`**:
    - [ ] **Check Hash**: Compare `sha256` of file on disk with `file_hash` in SQLite.
        - If match: Do nothing (idempotent).
        - If mismatch: Proceed to update.
    - [ ] **Cleanup Old Data**:
        - Query SQLite for all `Chunk`s associated with the `Document`.
        - Extract `chunk_id`s.
        - Delete from ChromaDB (`collection.delete(where={"chunk_id": ...})`).
        - Delete `Chunk`s and `Sentences` from SQLite.
    - [ ] **Re-Index**: Call `store_document` logic (Chunk -> Embed -> Store) for the new content.
    - [ ] Update `Document` record in SQLite with new hash.

## Client/Server Architecture (Planned)
**Reasoning:** To handle concurrency issues between long-running processes (MCP Server) and ephemeral ones (CLI Hooks, Admin CLI) accessing the same SQLite/ChromaDB files, we will move to a client-server model.

- [ ] **Implement Core REST API (`rag/server.py`)**
    - [ ] Use `FastAPI` to create a lightweight server.
    - [ ] **Endpoints**:
        - [ ] `POST /query`: Accepts query text, returns relevant chunks.
        - [ ] `POST /document`: Accepts file path/content, triggers indexing.
        - [ ] `PUT /document`: Triggers update/re-indexing.
        - [ ] `DELETE /document`: Removes document and embeddings.
        - [ ] `GET /status`: Returns DB stats (count of docs/chunks).
    - [ ] Manage the *single* connection to ChromaDB and SQLite here.

- [ ] **Refactor Integrations to use API**
    - [ ] **MCP Server**: Becomes a thin client that calls the REST API.
    - [ ] **Gemini CLI Hook**: A script that sends a generic `POST /query` to the running server.
    - [ ] **CLI Admin Tool**: A `typer`/`click` app that sends commands to the REST API.

## Update logic (re-adding of existing documents)
- [ ] **Implement `update_document(filename: str)` in `rag/manager.py`**:
    - [ ] **Check Hash**: Compare `sha256` of file on disk with `file_hash` in SQLite.
        - If match: Do nothing (idempotent).
        - If mismatch: Proceed to update.
    - [ ] **Cleanup Old Data**:
        - Query SQLite for all `Chunk`s associated with the `Document`.
        - Extract `chunk_id`s.
        - Delete from ChromaDB (`collection.delete(where={"chunk_id": ...})`).
        - Delete `Chunk`s and `Sentences` from SQLite.
    - [ ] **Re-Index**: Call `store_document` logic (Chunk -> Embed -> Store) for the new content.
    - [ ] Update `Document` record in SQLite with new hash.

## Legacy / Direct Library Tasks (On Hold/Deprecated by Server plan)
- [ ] *Create Entrypoint Script (Hook)* (Superseded by API client approach)
- [ ] *Create `server.py` MCP* (Superseded by API client approach)
- [ ] *CLI management interface* (Superseded by API client approach)
