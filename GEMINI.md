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
- **Search Strategy (Hybrid):**
  - **Semantic:** ChromaDB (Vector Search).
  - **Keyword:** BM25 (In-Memory Index).
  - **Fusion:** Reciprocal Rank Fusion (RRF) combines scores.
- **Storage Strategy (Parent-Child):**
  - **SQLite:** Stores full "Parent" text chunks (Scenes/Sessions).
  - **ChromaDB:** Stores "Child" vector embeddings (Sliding window of 3 sentences).

## Current Status (Feb 2026)

- **Fully Implemented:**
  - **Core Logic:** Hybrid Search, Parent-Child Retrieval, GPU Acceleration.
  - **Server:** FastAPI backend handles concurrent requests.
  - **Clients:** `rag-cli` (Admin), `rag-mcp` (IDE), Gemini Hooks (Context).
  - **Ingestion:** Markdown support with hash-based update detection.

- **In Progress / Planned:**
  - **Multi-Campaign Architecture:** Redesigning to support multiple independent campaigns stored in user profile (`~/.rag_dnd`).
  - **Client-Server Separation:** Moving prompt rendering logic to the server.

## Setup & Usage

### 1. Installation

Requires a NVIDIA GPU for optimal performance (using `cuda` device).

```bash
uv sync
```

### 2. Running the Server

Start the API server (Must be running for Hooks/CLI to work):

```bash
uv run rag-server
```

### 3. Integrations

- **Gemini CLI:** Automatically active via `rag-hook-context` if `.gemini/settings.json` has hooks enabled.
- **MCP:** Configure your IDE to run `uv run rag-mcp` in the project directory.

## Documentation Index

- **`doc/todo.md`**: Current technical task list and v0.x roadmap.
- **`doc/roadmap.md`**: Long-term vision and feature requests.
- **`doc/campaign_structure_design.md`**: Design document for the upcoming Multi-Campaign refactor.
- **`doc/llms.txt`**: References for Gemini CLI integration.
- **`doc/fastmcp.txt`**: Documentation for FastMCP module.
