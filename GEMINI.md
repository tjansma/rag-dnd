# rag-dnd

## Project Overview

**rag-dnd** is a Retrieval-Augmented Generation (RAG) system designed to index and query session logs from long-running Dungeons & Dragons campaigns.

The primary goal of this project is to integrate with the **Gemini CLI** via a **hook** (and IDEs via **MCP**). This integration automatically injects relevant campaign history into the context of prompts, ensuring the LLM is aware of past events, NPC interactions, and plot developments.

## Architecture & Technology

*   **Language:** Python (>=3.12)
*   **Package Manager:** `uv`
*   **Embeddings:** `intfloat/multilingual-e5-small` (optimized for Dutch & efficiency).
*   **Storage Strategy (Parent-Child):**
    *   **SQLite:** Stores full "Parent" text chunks (Scenes/Sessions).
    *   **ChromaDB:** Stores "Child" vector embeddings (Sliding window of 3 sentences).
*   **Core Libraries:**
    *   `langchain` / `langchain-huggingface`: For RAG abstractions.
    *   `chromadb`: Vector Store.
    *   `sqlalchemy`: ORM for SQLite.

## Current Status (Jan 2026)

- **Implemented:**
    - Markdown Header-based Chunking (`rag/chunker.py`).
    - Smart Sentence Splitting (`re` based).
    - E5 Embedding logic with Prefixes (`rag/embeddings.py`).
    - Storage Manager (`rag/manager.py`) orchestrating SQLite + Chroma.
    - Retrieval Logic (`rag/manager.py`).
- **In Progress:**
    - CLI Management Tools.
    - Integration Layers (Hooks & MCP).

## Setup & Usage

### Installation

```bash
uv sync
```

### Indexing Data

To parse and index the current log file (`config.session_log`):

```bash
python main.py
```

## Documentation

- **`doc/todo.md`**: Detailed technical roadmap and remaining tasks.
- **`doc/llms.txt`**: References for CLI integration.
