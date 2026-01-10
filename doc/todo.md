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

## Hook API for integrating into Gemini CLI
- [ ] **Create Entrypoint Script** (e.g., `hook.py` or entry in `main.py`)
    - [ ] Accept input arguments (the user's prompt to Gemini).
    - [ ] Run the `ParentChildRetriever` to find relevant D&D context.
    - [ ] **Format Output**:
        - Construct a "System Message" or "Context Block".
        - Example format:
          ```text
          <campaign_context>
          [Relevante Sessie Info 1...]
          [Relevante Sessie Info 2...]
          </campaign_context>
          ```
    - [ ] Print to `stdout` (so the Gemini CLI can capture and inject it).

## MCP Server API for integration into MCP Clients
- [ ] **Create `server.py`** using the `mcp-python` SDK.
- [ ] **Define Tools**:
    - [ ] `search_logs(query: str)`: Exposes the `ParentChildRetriever` logic to the AI.
- [ ] **Define Resources** (Optional):
    - [ ] `dnd://current_state`: Returns the summary of the latet session.
- [ ] **Transport**:
    - [ ] Configure Standard IO (stdio) transport for local use with Claude Desktop / Cursor / Windsurf.
- [ ] **Integration**:
    - [ ] Add configuration to `claude_desktop_config.json` or equivalent.

## CLI management interface (adding, removing, updating documents)
- [ ] **Using `click` or `typer` for CLI commands**:
    - [ ] `add <file>`: Calls `store_document`.
    - [ ] `update <file>`: Calls `update_document` (force check).
    - [ ] `remove <file>`:
        - Finds document by name.
        - Removes from SQLite and ChromaDB components.
    - [ ] `list`: Shows all indexed files + last update timestamp/hash.
    - [ ] `search <query>`: Quick CLI test for the Retriever.
