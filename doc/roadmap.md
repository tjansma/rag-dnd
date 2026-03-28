# Project Roadmap

This document outlines the vision and future features for the `rag-dnd` project.

## Completed (v0.1 - v0.3)

- [x] **Core RAG Logic**: Chunking, Embedding, Storage.
- [x] **GPU Acceleration**: Jina-v3 + CUDA 12.6.
- [x] **Backend API**: FastAPI v2 RESTful routes.
- [x] **Hybrid Search (BM25 + Vector RRF Fusion)**.
- [x] **Multi-Campaign Support**: Campaign CRUD, scoped storage & querying.
- [x] **Integrations**: Gemini CLI Hook, MCP Server, Admin CLI.
- [x] **Data & Config Separation**: Campaign data stored in user profile (`~/.rag_dnd/campaigns/`).

---

## 1. Structured D&D Data & Prompt Engine (v0.4 - v0.5)

The goal is to move from "Generic RAG" to a "Smart D&D Assistant" by adding mechanical awareness and persona consistency.

- [ ] **Phase 1: Structured Data (RDBMS)**
  - Models for Characters (PC/NPC/Monster) and Campaign State (Location/Date).
  - Implementation of a flexible JSON-blob for system-agnostic stats.
  - CRUD API and CLI for character management.
- [ ] **Phase 2: Prompt Engine & Handlers**
  - "The Orchestrator": A layer that combines Lore (RAG) and Stats (Structured Data).
  - **System Handlers**: Modular logic for calculating derived stats (e.g., D&D 5e modifiers).
  - **AI Triggers**: Dynamic persona shifts based on game state (e.g., "be aggressive if HP < 25%").

## 2. Automation & Workflow

- [ ] **Automatic Session Transcription**
  - Hook into Gemini CLI to log every prompt/response pair to a raw transcript file during gameplay.
- [ ] **Intelligent Summarization Pipeline**
  - Use LLM to summarize gameplay into narrative logbook entries.
  - Automatically index these entries into the RAG database.
- [ ] **Pub/Sub Architecture**
  - Implement a Publisher/Subscriber system to allow multiple independent agents/services to subscribe to game events.

## 3. Content Ingestion (PDF & Rules)

- [ ] **Advanced PDF Processing**
  - Smart chunking for D&D rulebooks and campaign modules.
  - Specialized handling for multi-column layouts, stat blocks, and tables.
- [ ] **Multi-Query Decomposition (v1.x)**
  - Upgrade Query Expansion to generate _multiple_ specific sub-queries from one user prompt to cover more semantic aspects.

## 4. Advanced AI Adaptation (Future)

- [ ] **Campaign-Specific LoRA Adapters**
  - Train lightweight LoRA adapters on campaign logs for better query enhancement and persona mimicry.
- [ ] **GraphRAG (Knowledge Graph Integration)**
  - Augment vector search with a graph database to enable multi-hop reasoning (e.g., "Who knows someone that hates the Zhentarim?").

---

## 5. Experimental / Visionary (Far Future)

- [ ] **Voice Mode (Speech-to-Speech)**
  - Real-time transcription and low-latency TTS for a hands-free DM experience.
- [ ] **Live DM HUD (Heads-Up Display)**
  - Real-time dashboard that proactively displays relevant statblocks, maps, and inventory based on the current context.

---

## 6. Infrastructure & CPU Optimization

- [ ] **Unified LLM Provider Abstraction**
  - Implement a common interface for different backends (`transformers`, `llama-cpp`, `ollama`).
  - Enable seamless switching between GPU-native (PyTorch) and CPU-optimized (GGUF) inference.
- [ ] **Full GGUF Pipeline**
  - Move both Embeddings (Jina-v3) and LLM (Qwen) to GGUF format for high-performance retrieval on low-resource VMs.
