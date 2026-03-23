# Project Roadmap

This document outlines the vision and future features for the `rag-dnd` project. Unlike `todo.md` (which tracks current generic tasks), this roadmap focuses on capability expansion.

## Completed (v0.1 - v0.3)

- [x] **Core RAG Logic**: Chunking, Embedding, Storage.
- [x] **GPU Acceleration**: Jina-v3 + CUDA 12.6.
- [x] **Backend API**: FastAPI v2 RESTful routes.
- [x] **Hybrid Search (BM25 + Vector RRF Fusion)**.
- [x] **Multi-Campaign Support**: Campaign CRUD, scoped storage & querying.
- [x] **Integrations**: Gemini CLI Hook, MCP Server, Admin CLI.
- [x] **Data & Config Separation**: Campaign data stored in user profile (`~/.rag_dnd/campaigns/`).
- [x] **Lazy CLI Configuration**: Supports global commands without prior campaign setup.
- [x] **Interactive Campaign Setup**: `campaign create` prompts for activation and auto-provisions directories.

## 1. Automation & Workflow

## 1. Multi-Query Decomposition (v1.x)

- Upgrade Query Expansion to generate _multiple_ specific sub-queries from one user prompt.
- Perform parallel vector searches for each sub-query.
- De-duplicate and re-rank results to cover multiple semantic aspects (e.g., "visuals" vs "dialogue").

## 2. Automation & Workflow

- [ ] **Automatic Session Transcription**
  - Hook into Gemini CLI to log every prompt/response pair to a raw transcript file during gameplay.
- [ ] **Intelligent Summarization Pipeline**
  - Workflow to read raw session transcripts.
  - Use LLM to summarize gameplay into narrative logbook entries.
  - Automatically index these entries into the RAG database.
  - Implement a Publisher/Subscriber architecture to decouple agent loop from RAG hooks.
  - Allow multiple independent agents/services to subscribe to game events.

- [ ] **Multi-Query Decomposition (v1.x)**
  - Upgrade Query Expansion to generate _multiple_ specific sub-queries from one user prompt.
  - Perform parallel vector searches for each sub-query.
  - De-duplicate and re-rank results to cover multiple semantic aspects (e.g., "visuals" vs "dialogue").

## 2. Multi-Campaign Architecture (v0.3 — Completed)

- [x] **Campaign CRUD** — `Campaign.create()`, `Campaign.list_all()`, `from_db_by_short_name()`.
- [x] **v2 RESTful API** — Campaign-scoped endpoints (`POST/GET /v2/campaigns`, `PUT/DELETE/POST .../documents`).
- [x] **Client Config** — `campaign` field in TOML, env var `RAG_DND_CAMPAIGN`, CLI `--campaign` flag.
- [x] **Document Model Refactor** — Removed `file_name`, chunker accepts `source_path: Path`.
- [x] **ChromaDB Naming** — `_-_` separator for collection names.
- [ ] **Data & Config Separation** (Deferred)
  - Store campaign data in user profile (`~/.rag_dnd/campaigns/`).
  - Separate application logic from content.
- [ ] **Prompt Engine** (Deferred)
  - Server-side rendering of System Prompts.
  - Dynamic injection of Character Sheets and Lore into context window.

## 3. Content Ingestion (PDF & Rules)

- [ ] **Advanced PDF Processing**
  - Smart chunking for D&D rulebooks and campaign modules.
  - specialized handling for:
    - Multi-column layouts
    - Stat blocks and Tables
    - Images/Maps
  - Ingestion pipeline to add these reference materials to the RAG.

## 4. Content Ingestion (PDF & Rules)

## 7. Advanced AI Adaptation (Future)

- [ ] **Campaign-Specific LoRA Adapters**
  - Train lightweight LoRA adapters on campaign logs (Domain Adaptation).
  - Use for **Query Enhancement**: Better translation of vague player intent to specific RAG queries.
  - **Per-Campaign Loading**: Hot-swap adapters based on the active campaign context.

## 8. Experimental / Visionary (Far Future)

- [ ] **GraphRAG (Knowledge Graph Integration)**
  - Augment vector search with a graph database (e.g., NetworkX/Neo4j).
  - Extract entities and relations (`(Jams)-[KNOWS]->(Nezznar)`) during ingestion.
  - Enable multi-hop reasoning questions ("Who knows someone that hates the Zhentarim?").
- [ ] **Voice Mode (Speech-to-Speech)**
  - **Input**: Real-time transcription using local Whisper.
  - **Output**: Low-latency TTS (e.g., XTTS/Piper) for the DM's voice.
  - Enable hands-free roleplay.
- [ ] **Live DM HUD (Heads-Up Display)**
  - Real-time dashboard that "listens" to the game state.
  - Proactively displays relevant statblocks, maps, and inventory without explicit queries.
  - "Zero-click" intelligence.
