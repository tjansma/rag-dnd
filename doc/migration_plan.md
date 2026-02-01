# Migration Plan: src-layout Refactor (COMPLETED)

**Status:** ✅ Completed on Feb 1, 2026.

This document outlines the step-by-step plan to refactor the `rag-dnd` repository from a flat script collection to a structured `src` package layout.

**Target Package Name:** `rag_dnd`

## Overview

We will perform this migration in 5 isolated phases. After each phase, we run a verification step to ensure no regression.

---

## Phase 1: Structure & Configuration

**Goal:** Create the directory skeleton and update build configuration.

1.  **Create Directories**:
    - `src/rag_dnd`
    - `src/rag_dnd/core`
    - `src/rag_dnd/server`
    - `src/rag_dnd/client`
    - `src/rag_dnd/cli`
    - `src/rag_dnd/hooks`
    - `src/rag_dnd/mcp`
2.  **Move Config**:
    - `config.py` (Server/Core config) -> `src/rag_dnd/core/config.py`
    - `client_config.py` (Client config) -> `src/rag_dnd/client/config.py`
3.  **Update `pyproject.toml`**:
    - Add `hatchling` build system.
    - Define entry points (even though they point to nothing yet).

**Verification:**

- Run `uv pip install -e .`
- Check if `import rag_dnd` works in python.

---

## Phase 2: Core Migration

**Goal:** Move the "Brain" (Database, Models, Logic) and fix imports.

1.  **Move Files**:
    - `rag/*` -> `src/rag_dnd/core/`
2.  **Refactor Imports**:
    - Update internal imports in `core/` to use relative (`.`) or absolute (`rag_dnd.core`) paths.
    - _Note:_ This breaks the external scripts temporarily.

**Verification:**

- Run a small script:
  ```python
  from rag_dnd.core.manager import RAGManager
  print("Core loaded successfully")
  ```

---

## Phase 3: Client Migration

**Goal:** Move the Client library.

1.  **Move Files**:
    - `rag_client/*` -> `src/rag_dnd/client/`
2.  **Refactor Imports**:
    - Update `client.py` to import from `rag_dnd.client.config`.

**Verification:**

- Run script:
  ```python
  from rag_dnd.client.client import RAGClient
  print("Client loaded")
  ```

---

## Phase 4: Server Migration

**Goal:** Move the FastAPI server.

1.  **Move Files**:
    - `api/*` -> `src/rag_dnd/server/`
2.  **Refactor Imports**:
    - Update routes to import from `rag_dnd.core...`.
3.  **Create Entry Point**:
    - Create `src/rag_dnd/server/main.py` (entry point function).

**Verification:**

- Run `rag-server` (via uv run).
- Check `http://localhost:8001/docs`.

---

## Phase 5: CLI & Hooks (Finalizing)

**Goal:** Convert scripts to package modules.

1.  **CLI**:
    - Move logic `rag-cli.py` -> `src/rag_dnd/cli/main.py`.
2.  **Hooks**:
    - Move `rag-hook.py` -> `src/rag_dnd/hooks/context.py`.
    - Move `rag-log-hook.py` -> `src/rag_dnd/hooks/logger.py`.
3.  **MCP**:
    - Move `rag-mcp-server.py` -> `src/rag_dnd/mcp/server.py`.
4.  **Cleanup**:
    - Delete old `.py` files in root.

**Verification:**

- Run `rag-cli --help`.
- Run `rag-hook-context` (test entry point).

---

## Rollback Plan

If anything fails catastrophically:

1.  Git checkout the commit before Phase 1.
2.  Delete `src/` directory.
