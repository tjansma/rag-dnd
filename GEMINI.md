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
- **Implemented:**
  - **Shared Core (`src/rag_dnd/core`):** Database models, Embeddings, Logic.
  - **FastAPI Server (`src/rag_dnd/server`):** Central entry point.
  - **Client Library (`src/rag_dnd/client`):** Python client for API.
  - **CLI Tools (`src/rag_dnd/cli`):** `rag-cli` command.
  - **Hooks (`src/rag_dnd/hooks`):** Gemini integration scripts.
  - **MCP Server (`src/rag_dnd/mcp`):** IDE integration.

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

### 2. Running the Server

Start the API server (Must be running for Hooks/CLI to work):

```bash
uv run rag-server
```

### 3. Gemini CLI Hook Setup

The project includes hooks to inject RAG context into Gemini CLI.

1.  **Enable Hooks Globally:**
    Ensure `C:\Users\<user>\.gemini\settings.json` has:

    ```json
    "tools": { "enableHooks": true }
    ```

2.  **Project Configuration:**
    The project `.gemini/settings.json` is configured to run `rag-hook-context` and `rag-hook-logger`.

3.  **Usage:**
    Just ask a question in Gemini CLI. The hook will:
    - Intercept the prompt.
    - Query the local RAG API.
    - Inject relevant logs as `additionalContext`.

### 4. CLI Tool

Manage documents via the command line:

```bash
# Add a document
uv run rag-cli rag add data/session_log.md

# Search manually
uv run rag-cli rag search "Wie is Nezznar?"
```

### 5. MCP Server Setup

To use the RAG system in Cursor or Claude Desktop:

1.  **Configure:** Add the server to your IDE's MCP settings (e.g., `claude_desktop_config.json` or `.gemini/settings.json`).

    ```json
    "mcpServers": {
      "rag-dnd": {
        "command": "uv",
        "args": [
          "--directory",
          "C:\\Development\\src\\_AI\\rag_dnd",
          "run",
          "rag-mcp"
        ]
      }
    }
    ```

## Documentation

- **`doc/todo.md`**: Detailed technical roadmap and remaining tasks.
- **`doc/llms.txt`**: References for Gemini CLI integration.
- **`doc/fastmcp.txt`**: Documentation for FastMCP module.
