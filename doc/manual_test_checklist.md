# Manual Functional Test Checklist (v1.0 Refactor)

Use this checklist to manually verify system functionality after each migration phase.

## 1. Core & Server Infrastructure

**Prerequisite:** API Server must be running for these tests (`rag-server`).

- [ ] **Startup Check**
  - [ ] Run `rag-server`.
  - [ ] Check logs for "Database initialized" and "Embeddings loaded".
  - [ ] Visit `http://localhost:8001/docs` in browser -> UI should load.

- [ ] **API Endpoints (via Swagger UI or Curl)**
  - [ ] `POST /v2/document` (Upload): Upload a new dummy `.md` file. Result: 200 OK.
  - [ ] `POST /rag_query` (Search): Query for content in that file. Result: JSON with chunks.
  - [ ] `PUT /v2/document` (Update): Modify file, re-upload via PUT. Result: 200 OK (no 409).
  - [ ] `DELETE /document`: Delete the file. Result: 200 OK.

---

## 2. CLI Tool (`rag-cli`)

**Command:** `rag-cli`

### RAG Operations

- [ ] **Upload**: `rag-cli rag upload data/LMoP_ToD_TimJansma_Log.md`
  - _Check:_ Output should show "Stored document" and chunk count > 0.
- [ ] **Search (Semantic)**: `rag-cli rag search "Wie is de smid?"`
  - _Check:_ Should return text results related to Phandalin/Smith.
- [ ] **Search (Hybrid/Keyword)**: `rag-cli rag search "Gundren Rockseeker"`
  - _Check:_ Should find exact name matches.

### Session & Campaign Management

- [ ] **Campaign List**: `rag-cli campaign list`
  - _Check:_ Should show table of campaigns and the "Active campaign" status at the bottom.
- [ ] **Campaign Create (Interactive)**: `rag-cli campaign create "Test" test "5e" "en"`
  - _Check:_ Should prompt to activate. Respond "y".
  - _Check:_ Directory `~/.rag_dnd/campaigns/test/` should be created.
- [ ] **Campaign Activate**: `rag-cli campaign activate <short_name>`
  - _Check:_ Should show success message and update active campaign in `config.toml`.
- [ ] **List Sessions**: `rag-cli session list`
  - _Check:_ Should show table of sessions from `transcript.db`.
- [ ] **Show Session**: `rag-cli session show 1`
  - _Check:_ Should print readable transcript of Session 1.
- [ ] **Export**: `rag-cli session export 1`
  - _Check:_ Should generate a Markdown file.

### Intelligence (LLM)

- [ ] **Summarize**: `rag-cli session summarize <ID>`
  - _Check:_ Should call Gemini/LLM and print summary (requires API key/LLM setup).
- [ ] **Expand Query**: `rag-cli llm expand "He went there"`
  - _Check:_ Should return expanded query ("Gundren went to Cragmaw Castle").

---

## 3. Hooks (Integration)

**These simulate the Gemini CLI interaction.**

### Context Hook (`rag-hook-context`)

- [ ] **Context Injection**:
  ```powershell
  # Windows PowerShell
  echo '{"session_id": "manual_test", "messages": [{"role": "user", "content": "Wie is Nezznar?"}]}' | rag-hook-context
  ```

  - _Check:_ JSON Output should contain `systemInstruction` with retrieved chunks about Nezznar.

### Logger Hook (`rag-hook-logger`)

- [ ] **Logging Interaction**:
  ```powershell
  # Windows PowerShell
  echo '{"session_id": "manual_test", "messages": [{"role": "user", "content": "Hi"}, {"role": "model", "content": "Hello"}]}' | rag-hook-logger
  ```

  - _Check:_ `data/transcript.db` should have a new turn for session `manual_test`.

---

## 4. MCP Server (`rag-mcp`)

- [ ] **Startup**: Run `rag-mcp`.
  - _Check:_ Process should start and wait for JSON-RPC input (no immediate error).
- [ ] **Inspector (Optional)**: Connect via `@modelcontextprotocol/inspector`.
  - _Check:_ Tools `rag_search`, `fetch_session` should be listed.
