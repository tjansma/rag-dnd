# rag-dnd

## Project Overview

**rag-dnd** is a Retrieval-Augmented Generation (RAG) system designed to index and query session logs from long-running Dungeons & Dragons campaigns.

The primary goal of this project is to integrate with the **Gemini CLI** via a **hook**. This integration will automatically inject relevant campaign history into the context of every new prompt, ensuring the LLM is aware of past events, NPC interactions, and plot developments during the session.

## Architecture & Technology

*   **Language:** Python (>=3.12)
*   **Package Manager:** `uv`
*   **Core Libraries:**
    *   `fastapi`: For the API layer.
    *   `langchain`: For RAG orchestration.
    *   `chromadb`: Vector Store.
    *   `sentence-transformers`: Embeddings.
*   **Integration:** Gemini CLI Hooks (see `doc/llms.txt` for CLI architecture references).

## Setup & Usage

### Installation

This project uses `uv` for dependency management.

```bash
uv sync
```

### Running

Currently, the project entry point is a simple placeholder.

```bash
python main.py
```

## Development Context

*   **Configuration:** Managed via `pyproject.toml`.
*   **Documentation:** References for LLM integration and CLI architecture are located in `doc/`.
*   **Goal:** Implement the RAG logic in Python and expose it via a script or API that the Gemini CLI hook can call to retrieve context before sending a prompt to the model.
