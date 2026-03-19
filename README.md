# rag-dnd

A **Retrieval-Augmented Generation (RAG)** system built to provide context-aware responses for Dungeons & Dragons campaigns. This project indexes long-running campaign logs and injects relevant session history into LLM prompts via the Gemini CLI or MCP-compatible editors.

## 🚀 Features

- **SOTA Embeddings:** Uses `jina-embeddings-v3` (8192 context length, multilingual) powered by **CUDA 12.6**.
- **Hybrid Search:** Combines **Semantic Search** (Vector) with **Keyword Search** (BM25) using Reciprocal Rank Fusion (RRF) for optimal recall of both themes and specific names.
- **Narrative Aware:** Parent-Child retrieval ensures context is never lost at sentence boundaries.
- **Dual-Store Architecture:** Source of truth in SQLite, vectors in ChromaDB.
- **High Performance:** GPU acceleration for embedding generation (20-50x speedup).
- **Multi-Campaign:** Campaign-scoped document storage, querying, and management via v2 RESTful API.
- **Client Ecosystem:**
  - **Gemini CLI Hook:** Auto-injects campaign-aware context into `gemini` prompts.
  - **MCP Server:** Provides "Search Logs" tools to Claude, Cursor, and other IDEs.
  - **CLI Tool:** Administrative commands for ingestion, management, and campaign CRUD.

## 🏗️ Architecture

The system uses a **Client-Server** model to allow concurrent access to the knowledge base:

1.  **Backend (FastAPI):** Single "Gatekeeper" process managing SQLite/ChromaDB connections.
2.  **Clients:** Admin CLI, Gemini Hook, and MCP Server all communicate via the REST API.

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
uv run rag-server
```

The server will start on `http://localhost:8001`.

### 2. Campaign Setup

Create a campaign and configure it:

```bash
# Create a campaign
uv run rag-cli campaign create "Lost Mine of Phandelver" lmop_tod "D&D 5e" "nl"

# Upload a document
uv run rag-cli --campaign lmop_tod rag upload data/session_log.md
```

### 3. Querying

Perform a search against the knowledge base:

```bash
# Via CLI
uv run rag-cli rag search "Wie is Nezznar?"

# Via API (v2)
curl -X POST "http://localhost:8001/v2/campaigns/lmop_tod/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "Wat weet Jams over de Black Spider?"}'
```

## 🗺️ Roadmap & Status

- [x] **Core RAG Logic:** Chunking, Embedding, Storage.
- [x] **GPU Acceleration:** Jina V3 + CUDA 12.6.
- [x] **Backend API:** FastAPI v2 RESTful routes.
- [x] **Hybrid Search:** BM25 + Vector RRF Fusion.
- [x] **Multi-Campaign Support:** Campaign CRUD, scoped storage & querying.
- [x] **Integrations:** Gemini CLI Hook, MCP Server, Admin CLI (all campaign-aware).
- [ ] **Prompt Engine:** Server-side system prompt rendering.

See `doc/todo.md` for the technical task list and `doc/roadmap.md` for the long-term vision.
