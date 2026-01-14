# rag-dnd

A **Retrieval-Augmented Generation (RAG)** system built to provide context-aware responses for Dungeons & Dragons campaigns. This project indexes long-running campaign logs and injects relevant session history into LLM prompts via the Gemini CLI or MCP-compatible editors.

## Architecture & Technology

*   **Language:** Python (>=3.12)
*   **Package Manager:** `uv`
*   **Backend:** FastAPI Server (`api/`)
*   **Embeddings:** `jinaai/jina-embeddings-v3` (SOTA, GPU Accelerated).
*   **Storage:**
    *   **SQLite:** Stores full "Parent" text chunks (Scenes/Sessions).
    *   **ChromaDB:** Stores "Child" vector embeddings (Sliding window of 3 sentences).

### Client/Server Architecture

To support multiple simultaneous interfaces (Gemini CLI Hook, MCP Server, Admin CLI) without file locking issues on the local SQLite/Chroma databases, the system uses a central API:

1.  **Backend (FastAPI):** Single "Gatekeeper" process managing all DB connections.
2.  **Clients:**
    *   **Admin CLI:** For adding/updating log files.
    *   **Gemini Hook:** For injecting context into CLI chats.
    *   **MCP Server:** For exposing tools to AI assistants (Claude, Cursor, etc.).

## 🚀 Features

- **SOTA Embeddings:** Uses `jina-embeddings-v3` (8192 context length, multilingual) powered by **CUDA 12.6**.
- **Narrative aware:** Parent-Child retrieval ensures context is never lost at sentence boundaries.
- **Dual-Store Architecture:** Source of truth in SQLite, vectors in ChromaDB.
- **High Performance:** GPU acceleration for embedding generation (20-50x speedup).
- **Concurrency Safe:** Central FastAPI server handles all database IO.

## 🛠️ Installation

This project uses `uv` for dependency management and requires an NVIDIA GPU for best performance.

```bash
# 1. Clone the repository
git clone <repo-url>
cd rag-dnd

# 2. Sync dependencies (Autodetects CUDA)
uv sync
```

Ensure you have NVIDIA Drivers installed supporting CUDA 12.6+.

## 📖 Usage

### 1. Start the Server
The central API must be running for any clients to work.

```bash
uv run -m api
```
The server will start on `http://localhost:8000`.

### 2. Indexing Data
You can index documents via the API (CLI tool coming soon).

```bash
# Example using curl
curl -X POST "http://localhost:8000/document" \
     -H "Content-Type: application/json" \
     -d '{"file_path": "C:/path/to/session_log.md"}'
```

### 3. Querying
Perform a search against the knowledge base:

```bash
curl -X POST "http://localhost:8000/rag_query" \
     -H "Content-Type: application/json" \
     -d '{"query": "Wat weet Jams over de Black Spider?"}'
```

## 🗺️ Roadmap

- [x] **Core RAG Logic:** Chunking, Embedding, Storage.
- [x] **GPU Acceleration:** Jina V3 + CUDA 12.6.
- [x] **Backend API:** FastAPI implementation.
- [ ] **CLI Interface:** `rag-cli` for easy management.
- [ ] **Gemini Hook:** Script to intercept specific prompt patterns.
- [ ] **MCP Server:** Implementation of `search_logs` tool for IDEs.

See `doc/todo.md` for the detailed technical task list.
