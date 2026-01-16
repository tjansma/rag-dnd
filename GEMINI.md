# rag-dnd

## Project Overview

**rag-dnd** is a Retrieval-Augmented Generation (RAG) system designed to index and query session logs from long-running Dungeons & Dragons campaigns.

The primary goal of this project is to integrate with the **Gemini CLI** via a **hook** (and IDEs via **MCP**). This integration automatically injects relevant campaign history into the context of prompts, ensuring the LLM is aware of past events, NPC interactions, and plot developments.

## Architecture & Technology

- **Language:** Python (>=3.12)
- **Package Manager:** `uv`
- **API:** FastAPI (Backend Server)
- **Embeddings:**
  - `jinaai/jina-embeddings-v3` (SOTA 8192-token context, GPU accelerated).
  - Fallback: `intfloat/multilingual-e5-base`.
- **Hardware Acceleration:** NVIDIA CUDA 12.6 support (torch 2.9.1+cu126).
- **Storage Strategy (Parent-Child):**
  - **SQLite:** Stores full "Parent" text chunks (Scenes/Sessions).
  - **ChromaDB:** Stores "Child" vector embeddings (Sliding window of 3 sentences).
- **Core Libraries:**
  - `fastapi`: REST API for concurrent access.
  - `langchain` / `langchain-huggingface`: For RAG abstractions.
  - `chromadb`: Vector Store.
  - `sqlalchemy`: ORM for SQLite.

## Current Status (Jan 2026)

- **Implemented:**
  - **FastAPI Backend (`api/`):** Central server managing DB access.
  - **Jina V3 Integration:** GPU-accelerated embeddings with `trust_remote_code=True`.
  - **RAG Core (`rag/`):**
    - Markdown Header-based Chunking (`rag/chunker.py`).
    - Smart Sentence Splitting.
    - Storage Manager (`rag/manager.py`) orchestrating SQLite + Chroma.
  - **Clients:**
    - **CLI:** `rag-cli.py` for document management.
    - **Gemini Hook:** `rag-hook.py` for context injection.
- **Planned:**
  - **MCP Server:** To expose RAG capabilities to IDEs like Cursor/Claude.

## Setup & Usage

### 1. Installation

Requires a NVIDIA GPU for optimal performance (using `cuda` device).

```bash
# Install dependencies (auto-detects CUDA 12.6)
uv sync

# Configure .env (optional, defaults provided in config.py)
# RAG_DND_EMBEDDINGS_MODEL=jinaai/jina-embeddings-v3
# RAG_DND_EMBEDDINGS_DEVICE=cuda
```

### 2. Running the Server

Start the API server (Must be running for Hooks/CLI to work):

```bash
uv run api
```

### 3. Gemini CLI Hook Setup

The project includes a hook to inject RAG context into Gemini CLI.

1.  **Enable Hooks Globally:**
    Ensure `C:\Users\<user>\.gemini\settings.json` has:

    ```json
    "tools": { "enableHooks": true }
    ```

2.  **Project Configuration:**
    The project `.gemini/settings.json` is pre-configured to run `rag-hook.py`.
    _Note: It uses a direct path to the `.venv` python executable to avoid timeouts._

3.  **Usage:**
    Just ask a question in Gemini CLI. The hook will:
    - Intercept the prompt.
    - Query the local RAG API.
    - Inject relevant logs as `additionalContext`.

### 4. CLI Tool

Manage documents via the command line:

```bash
# Add a document
uv run rag-cli.py add data/session_log.md

# Search manually
uv run rag-cli.py search "Wie is Nezznar?"
```

## Documentation

- **`doc/todo.md`**: Detailed technical roadmap and remaining tasks.
- **`doc/llms.txt`**: References for Gemini CLI integration.
- **`doc/fastmcp.txt`**: Documentation for FastMCP module.
