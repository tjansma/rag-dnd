# rag-dnd

## Project Overview

**rag-dnd** is a Retrieval-Augmented Generation (RAG) system designed to index and query session logs from long-running Dungeons & Dragons campaigns.

The primary goal of this project is to integrate with the **Gemini CLI** via a **hook** (and IDEs via **MCP**). This integration automatically injects relevant campaign history into the context of prompts, ensuring the LLM is aware of past events, NPC interactions, and plot developments.

## Architecture & Technology

*   **Language:** Python (>=3.12)
*   **Package Manager:** `uv`
*   **API:** FastAPI (Backend Server)
*   **Embeddings:** 
    *   `jinaai/jina-embeddings-v3` (SOTA 8192-token context, GPU accelerated).
    *   Fallback: `intfloat/multilingual-e5-base`.
*   **Hardware Acceleration:** NVIDIA CUDA 12.6 support (torch 2.9.1+cu126).
*   **Storage Strategy (Parent-Child):**
    *   **SQLite:** Stores full "Parent" text chunks (Scenes/Sessions).
    *   **ChromaDB:** Stores "Child" vector embeddings (Sliding window of 3 sentences).
*   **Core Libraries:**
    *   `fastapi`: REST API for concurrent access.
    *   `langchain` / `langchain-huggingface`: For RAG abstractions.
    *   `chromadb`: Vector Store.
    *   `sqlalchemy`: ORM for SQLite.

## Current Status (Jan 2026)

- **Implemented:**
    - **FastAPI Backend (`api/`):** Central server managing DB access.
    - **Jina V3 Integration:** GPU-accelerated embeddings with `trust_remote_code=True`.
    - **Automatic Versioning:** ChromaDB collections are versioned by model name (`rag_dnd_jinaai_...`).
    - **RAG Core (`rag/`):**
        - Markdown Header-based Chunking (`rag/chunker.py`).
        - Smart Sentence Splitting.
        - Storage Manager (`rag/manager.py`) orchestrating SQLite + Chroma.
- **Planned:**
    - **Thin Clients:** CLI tools, MCP server, and Hooks to consume the REST API.

## Setup & Usage

### Installation

Requires a NVIDIA GPU for optimal performance.

```bash
# 1. Install dependencies (auto-detects CUDA 12.6)
uv sync

# 2. Configure .env (optional, defaults provided in config.py)
# RAG_DND_EMBEDDINGS_MODEL=jinaai/jina-embeddings-v3
# RAG_DND_EMBEDDINGS_DEVICE=cuda
```

### Running the Server

Start the API server:
```bash
uv run api
```

### Indexing Data (via API)

Use CURL or Postman to ingest logs:
```bash
curl -X POST "http://localhost:8000/document" \
     -H "Content-Type: application/json" \
     -d '{"file_path": "data/session_log.md"}'
```

## Documentation

- **`doc/todo.md`**: Detailed technical roadmap and remaining tasks.
- **`doc/llms.txt`**: References for Gemini CLI integration.
- **`doc/fastmcp.txt`**: Documentation for FastMCP module.
