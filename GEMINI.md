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

## Module Structure

The codebase is organized into domain-specific modules with a shared `core`:

```
src/rag_dnd/
    campaign.py        # Top-level Application Facade orchestrating core, rag, and game
    core/              # Shared infrastructure (ORMBase, CampaignMetadata, database sessions)
    rag/               # RAG-specific logic (embeddings, chunking, vector store, hybrid search)
    game/              # Structured D&D data (characters, sessions, players, assets)
    server/            # FastAPI backend (routes, schemas, dependencies)
    client/            # Client library (ClientConfig, API client, transcript)
    cli/               # CLI tool (Click-based admin interface)
    hooks/             # Gemini CLI hooks (context injection, logging)
```

### Core Module (`core/`)
- `database.py`: SQLAlchemy engine singleton, session management (`get_session()`), `init_db()`.
- `models.py`: `ORMBase` (declarative base), `CampaignMetadata` (shared across rag & game).

### RAG Module (`rag/`)
- `models.py`: `Collection`, `Document`, `Chunk`, `Sentence`, `QueryResult`.
- `manager.py`: High-level RAG operations (store, delete, query).
- `store.py`: `VectorStore` (ChromaDB + BM25 hybrid search).
- `embeddings.py`: Embedding generation (jina-embeddings-v3).
- `chunker.py`: Markdown → Chunks (heading-based splitting).

### Game Module (`game/`)
- `enums.py`: `CharacterType`, `Disposition`, `RelationshipType`, `AssetType`, `PlayerType`.
- `models.py`: All structured D&D data models:
  - **Standalone:** `Player` (global), `GameCharacter`, `Asset`, `GameSession`, `Turn`.
  - **Link tables:** `PlayerCharacter`, `CharacterRelationship`, `CampaignAsset`, `CharacterAsset`, `TurnCharacter`, `SessionAsset`, `ChunkCharacter`.

## Current Status (April 2026)

- **Fully Implemented:**
  - **Core Logic:** Hybrid Search, Parent-Child Retrieval, GPU Acceleration.
  - **Server:** FastAPI backend with v2 RESTful campaign-scoped API.
  - **Multi-Campaign:** `Campaign` CRUD, scoped document storage & querying.
  - **v2 API:** `POST/GET /v2/campaigns`, `PUT/DELETE .../documents`, `POST .../query`.
  - **Clients:** `rag-cli` (Admin + `--campaign` flag), `rag-mcp` (IDE), Gemini Hooks (Context).
    All campaign-aware via shared `ClientConfig`.
  - **Data Separation:** Campaign data and logs stored in user profile (`~/.rag_dnd/campaigns/`).
  - **Lazy CLI Configuration:** Admin and listing commands work without a pre-set campaign.
  - **Campaign Management:** `campaign activate` for easy switching; `campaign create` auto-provisions directories.
  - **Ingestion:** Markdown support with hash-based update detection.
    Chunker decoupled from ORM (`source_path: Path` parameter).
  - **Cross-Platform Setup:** `setup.ps1` and `setup.sh` automate installation, configuration, and launcher creation.
  - **Gemini CLI Integration:** Automatic path configuration for hooks and MCP in `.gemini/settings.json`.
  - **Session Management:** Context-managed database sessions with singleton engine,
    `_store_impl`/`_delete_impl` helpers for transactional integrity, and
    `expire_on_commit=False` for safe detached object access.
  - **Error Handling:** Domain exceptions (`DocumentExistsError`, `DocumentNotFoundError`)
  - **Modular Architecture (Phase 1):** Extracted `ORMBase`, `CampaignMetadata`, and database engine out of `rag/` into `core/`. Established `Campaign` as a top-level Application Facade to cleanly orchestrate RAG and game logic.
  - **Structured D&D Data Models (v0.4):** Implemented 5 enums and 11 new SQLAlchemy models in `game/models.py` (characters, sessions, players, assets, junction tables).
  - **Pragmatic Monolith & 3NF:** Seamlessly linked `rag`, `core`, and `game` domains using strict 3NF Junction Tables (`GameCharacterRAGDocument` etc.) and string-based ORM relationships to guarantee integrity while preventing circular dependencies.
  - **Player API (Phase 5a):** Implemented an end-to-end Player API (REST routes, Discriminated Union schemas, auto-generated Pydantic client models, and a structured Typer CLI `rag-cli player`).

- **In Progress (API/CLI Rollout):**
  - **Character API (Phase 5b):** **[GOAL FOR NEXT SESSION]** Implement CRUD endpoints (`routes_v2.py`), Pydantic schemas, and CLI commands for `GameCharacter` and its relationships.

- **Planned:**
  - **Session & Turn API:** Endpoints to manage play sessions. 
  - **Transcript Migration:** Move session transcripts from client-side `transcript.db` to server-side `GameSession`/`Turn` models.
  - **Asset Management:** APIs for the Global Asset Library.
  - **Prompt Engine (v0.5):** Server-side rendering of system prompts with auto-injected character state.

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
- **`doc/prompt_engine/`**: Design documents for structured data, character system, and prompt engine.
- **`doc/campaign_structure_design.md`**: Design document for the Multi-Campaign architecture.
- **`doc/llms.txt`**: References for Gemini CLI integration.
- **`doc/fastmcp.txt`**: Documentation for FastMCP module.
