# Project Roadmap

This document outlines the vision and future features for the `rag-dnd` project. Unlike `todo.md` (which tracks current generic tasks), this roadmap focuses on capability expansion.

## 1. Automation & Workflow

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

## 2. Content Ingestion (PDF & Rules)

- [ ] **Advanced PDF Processing**
  - Smart chunking for D&D rulebooks and campaign modules.
  - specialized handling for:
    - Multi-column layouts
    - Stat blocks and Tables
    - Images/Maps
  - Ingestion pipeline to add these reference materials to the RAG.

## 3. Structured Data & Character Tracking

- [ ] **Relational Character Database**
  - Move beyond text-only tracking for critical stats.
  - Schema for:
    - Ability Scores, Saving Throws, Skills.
    - Inventory, Gold, Equipment.
    - HP, AC, Conditions.
- [ ] **State Tracking Hooks**
  - Mechanisms to update this DB based on narrative events (e.g., "I buy a potion" -> deduct gold, add item).

## 4. Interfaces & Management

- [ ] **Web Administration Interface**
  - GUI overview of the RAG content types and collections.
  - Drag-and-drop upload for documents and manuals.
  - Visual editing of chunks or headers.
- [ ] **CLI Tool Expansion**
  - Advanced management commands (re-index specific collections, prune partial data).
- [ ] **Full MCP & Hook Ecosystem**
  - Expose Character DB and Rule lookups solely via MCP/Hooks to the AI.
- [ ] **Multipart File Uploads**
  - Refactor API to support `multipart/form-data` for robust file handling.

## 5. Search Intelligence

- [x] **Hybrid Search (BM25 + Semantic)**
  - Implement **In-Memory BM25** using `rank_bm25` (Ensemble Retriever).
  - Implement **Reciprocal Rank Fusion (RRF)** to combine Jina-v3 vectors with BM25 scores.
