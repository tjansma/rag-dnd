# rag-dnd

A **Retrieval-Augmented Generation (RAG)** system built to provide context-aware responses for Dungeons & Dragons campaigns. This project indexes long-running campaign logs and injects relevant session history into LLM prompts via the Gemini CLI or MCP-compatible editors.

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
    *   `fastapi`: (Planned) REST API to handle concurrent access.

### Planned System Design (Client/Server)

To support multiple simultaneous interfaces (Gemini CLI Hook, MCP Server, Admin CLI) without file locking issues on the local SQLite/Chroma databases, the system will evolve into a client-server architecture:

1.  **Backend (FastAPI):** Single "Gatekeeper" process managing all DB connections.
2.  **Clients:**
    *   **Admin CLI:** For adding/updating log files.
    *   **Gemini Hook:** For injecting context into CLI chats.
    *   **MCP Server:** For exposing tools to AI assistants (Claude, Cursor, etc.).

## 🧠 Core Concept: Parent-Child RAG

To handle narrative data effectively, we use a **Parent-Child** retrieval strategy:
1.  **Parent Chunks (Context):** The system stores full session summaries or scenes (large chunks) in a SQLite database.
2.  **Child Chunks (Search):** It splits these scenes into small, overlapping windows of sentences (3 sentences).
3.  **The Trick:** We embed the *sentences* for precise searching, but the search result links back to the *parent*.
    *   *Query:* "Wie heeft de hamer Betsy?"
    *   *Match:* (Sentence) "Harley zwaait met Betsy..."
    *   *Result:* The **entire scene/session** where this happens, giving the LLM full context of the fight, location, and allies.

## 🚀 Features

- **Smart Indexing:** Uses `intfloat/multilingual-e5-small` for high-quality, efficient Dutch embeddings.
- **Narrative aware:** Sliding window chunking ensures context is never lost at sentence boundaries.
- **Dual-Store Architecture:**
    - **SQLite:** Stores the "Source of Truth" (Parent Texts).
    - **ChromaDB:** Stores the vectors (Child Embeddings + Pointers).
- **Client/Server Model:** Central API ensuring safe concurrent access.
- **Gemini CLI Integration:** (Planned) Automatically injects context into your terminal chat.
- **MCP Server:** (Planned) Exposes RAG capabilities to Claude Desktop, Cursor, and Windsurf.

## 🛠️ Installation

This project uses `uv` for modern, fast Python dependency management.

```bash
# 1. Clone the repository
git clone <repo-url>
cd rag-dnd

# 2. Sync dependencies
uv sync
```

## 📖 Usage

### Indexing a Log File
Currently, the `main.py` script indexes the session log defined in `config.py`.

```bash
python main.py
```
This will:
1.  Read the markdown log.
2.  Split it into header-based sections (Parents).
3.  Split sections into sentence windows (Children).
4.  Generate embeddings and populate `data/chroma_db` and `data/dnd.db`.

### Querying
You can currently query the logs using the Python API in `main.py` or `rag.manager.query`.
A full CLI interface is planned:
```bash
# Future usage
python cli.py search "Wat weet Jams over de Black Spider?"
```

## 🗺️ Roadmap

- [x] **Core RAG Logic:** Chunking, Embedding, Storage.
- [x] **Retriever:** Logic to query the database and return Parent chunks.
- [ ] **CLI Interface:** `add`, `remove`, `update`, `search` commands.
- [ ] **Gemini Hook:** Script to intercept specific prompt patterns.
- [ ] **MCP Server:** Implementation of `search_logs` tool for IDEs.

See `doc/todo.md` for the detailed technical task list.
