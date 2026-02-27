# Campaign System Design Analysis

## Current State Analysis

The current `rag-dnd` system is designed as a single-instance application.

- **Configuration**: `src/rag_dnd/config.py` contains hardcoded default paths pointing to `data/session_log.txt`, `data/chroma`, etc.
- **Data Storage**: All data resides in the root `data/` directory, mixing database files, logs, and potentially other assets.
- **Prompts**: `prompts/game/instructions.j2` is a powerful Jinja2 template that expects a structured `campaign` object (PC, party members, docs), but there is currently no obvious mechanism to inject this data dynamically per campaign other than potentially hardcoding it or modifying the code.

## Proposed Campaign Structure

To support multiple campaigns and separate user data from application code, data will be stored in the user's home directory (e.g., `~/.rag_dnd/` or `%APPDATA%/rag_dnd/`).

### Directory Layout

```text
~/.rag_dnd/ (or %APPDATA%/rag_dnd/)
├── settings.json                   # Global user preferences (already exists)
└── campaigns/
    └── [campaign_id]/              # e.g., "curse_of_strahd"
        ├── campaign.yaml           # Metadata: Name, setting, PC info, active party
        ├── session_log.md          # The main chronologial log (Parent chunks)
        ├── summary.md              # The concise summary (Current status)
        ├── db/                     # Campaign-specific databases
        │   ├── chroma/             # Vector store for this campaign
        │   └── transcript.db       # SQLite database for this campaign
        ├── characters/             # Character sheets/data
        │   ├── [pc_name].md
        │   ├── [pc_name].yaml      # Optional: structured stats
        │   └── [npc_name].md
        └── docs/                   # Lore, handouts, world info
            ├── world_map.md
            └── faction_notes.md
```

### `campaign.yaml` Definition

This file will serve as the "Configuration Source of Truth" for the campaign, populating the `instructions.j2` template.

```yaml
name: "Curse of Strahd"
language: "Dutch"
system: "D&D 5e"

# Paths relative to campaign root
files:
  session_log: "session_log.md"
  summary: "summary.md"

pc:
  name: "Jams Capbarren"
  character_sheet: "characters/jams.md"
  # Structured data for jinja context
  pronouns: "his"

party_members:
  - name: "Ismark"
    character_sheet: "characters/ismark.md"
  - name: "Ireena"
    character_sheet: "characters/ireena.md"

docs:
  - name: "Barovia Lore"
    path: "docs/barovia_guide.md"
    description: "General knowledge about the land of Barovia"
```

## Required System Changes

To implement this without breaking existing functionality ("basis-systeem"), we need to abstract the configuration.

1.  **Context Switching**:
    - The `Config` class in `src/rag_dnd/config.py` needs to dynamically resolve the `campaign_root`.
    - Default location becomes `Path.home() / ".rag_dnd" / "campaigns" / [campaign_id]`.
    - All database paths (`chroma`, `sqlite`) should be resolved relative to this `campaign_root`.

2.  **Prompt Generation (`instructions.j2`)**:
    - We need a loader that reads `campaign.yaml` and constructs the context dictionary required by `instructions.j2`.
    - The `{{ campaign.summary_file }}` variable in the template currently assumes a filename. In the new system, it should probably point to the _content_ or the _absolute path_ that the LLM tools can access.

3.  **CLI / API**:
    - The commands need a way to target a campaign.
    - `uv run rag-cli --campaign curse_of_strahd add ...`
    - Or set an ENV variable: `RAG_CAMPAIGN=curse_of_strahd`.

## LLM Prompts & Generation

The user requested "duidelijke prompts voor het LLM voor binnen die campaign genereren".

The current `instructions.j2` is excellent but complex. To optimize it for generation within a specific campaign:

1.  **System Prompt**: The rendered `instructions.j2` output (filled with `campaign.yaml` data) becomes the System Prompt.
2.  **Dynamic Context**: The "Concise Summary" (`summary.md`) is injected into the context window (as it is now).
3.  **RAG Context**: Retrieved chunks from `session_log.md` (via Chroma) are injected as "Memories".

**Optimization**:

- Move generic rules (Dice rolling, formatting) to a static `base_instructions.md`.
- Keep the `campaign.yaml` driven part as `campaign_context.md`.
- Combine them at runtime: `System Prompt = Base Rules + Campaign Context`.

## Next Steps (Analysis Phase)

1.  Confirm if the user wants to migrate existing data (`LMoP_ToD_TimJansma_Log.md`) into this new structure immediately or start fresh.
2.  Decide if the `rag-server` should serve _one_ campaign at a time (simpler) or _multiple_ (complex API routing). Given this is a personal tool, running one instance per active campaign (or restarting to switch) is often acceptable and much simpler to build.

## Client-Server Data Separation

To maintain a clean architecture, we will strictly distinguish between **Data (Storage)** and **Behavior (Logic)** within the backend, as well as separating Server Data from Client Data.

### Backend Responsibilities: Datamodels vs. Business Logic

1.  **`CampaignMetadata` (The ORM Model in `models.py`)**
    - **Purpose**: Purely defines the schema for SQLite (the "Registration").
    - **Responsibility**: Reading and writing strings/ints to the `campaign_metadata` table.
    - **Knowledge**: Knows _what_ the file paths are (e.g., `session_log_file`), but cannot open or interact with them. It knows nothing of Markdown, YAML, or Jinja.

2.  **`Campaign` (The Service Class in `campaign.py`)**
    - **Purpose**: The active "Game Master" engine for a running session.
    - **Responsibility**: Orchestrating I/O, file management, and LLM orchestration for a specific campaign. All operations run within the scope of a single campaign instance.
    - **Architecture**: Acts as a wrapper around `CampaignMetadata`. It uses the paths stored in the metadata to actually read/write files.
    - **Construction** (Classmethod pattern):
      - `__init__(self, metadata: CampaignMetadata)`: Simple constructor, accepts only the finished metadata object.
      - `from_db_by_id(cls, id)`: Load from database by ID.
      - `from_db_by_short_name(cls, name)`: Load from database by short name.
      - `from_yaml(cls, path)`: Bootstrap a _new_ campaign from a `campaign.yaml` file (import/first-time setup only; the database is the runtime source of truth, not the YAML).
    - **Behavior** (methods absorb functionality from the legacy `manager.py`):
      - `store_document(filename)`: Index a document into this campaign's collection and vector store.
      - `delete_document(filename)`: Remove a document from this campaign's stores.
      - `update_document(filename)`: Re-index a changed document (hash check → delete + store).
      - `query(query_text)`: Hybrid search scoped to this campaign's vector store.
      - `add_to_session_log(text)`: Append to the session log file and trigger re-indexing.
      - `generate_summary()`: Read the log, call the LLM, overwrite the active summary file.
      - `get_system_prompt()`: Read character sheets and base prompts, assemble dynamically.

3.  **`manager.py` (Legacy → To Be Absorbed)**
    - Written before the multi-campaign architecture. Contains loose functions (`store_document`, `query`, etc.) that operate on global defaults (`Config.load()`, `get_session()`).
    - These functions will be migrated into `Campaign` methods incrementally. The migration can happen gradually: the `Campaign` methods can initially _delegate_ to `manager.py` functions, then absorb them over time.
    - After migration, only truly campaign-agnostic utilities (e.g., `expand_query`, `prompt_llm`) remain and move to `llm.py` or similar. `manager.py` and `services.py` can then be removed.

### Server Responsibility (The "Host")

The **RAG Server** is the sole owner of the `~/.rag_dnd/campaigns/` directory.

- **Storage**: Manages all databases (SQLite, Chroma), logs (`session_log.md`), and assets (`campaign.yaml`).
- **Logic**: Handles ingestion, retrieval, and _prompt construction_.
- **Access**: Clients should **NEVER** read files in this directory directly. They must request data via the API.
  - _Why?_ This allows the server to change file formats or storage backends without breaking the client. It also enables remote clients (e.g., a laptop connecting to a desktop server).

### Client Responsibility (The "Interface")

The **Client** (CLI, Gemini Hook, MCP) owns its local configuration, typically in `~/.config/rag_dnd/client.toml` or `~/.rag_dnd/client_config.toml` (mirroring the server path root implies a shared home, but conceptually they are distinct).

- **Configuration**: Stores `api_url`, `api_key` (future), and `active_campaign_id`.
- **State**: May cache minimal data but relies on the Server for truth.
- **Workflow**:
  1.  Client: "I need to start a session for campaign X." -> `GET /campaigns/X/context`
  2.  Server: Reads `campaign.yaml` + `summary.md`, renders the System Prompt templte, and returns the full System Prompt string.
  3.  Client: Sends System Prompt to LLM tool (Gemini).

### Proposed API Additions for Separation

To support this, the API needs:

- `GET /campaigns`: List available campaigns.
- `POST /campaigns/{id}/activate`: Switch active context (if single-tenant) or specificy context.
- `GET /campaigns/{id}/system-prompt`: **Crucial**. Returns the fully rendered instructions including the concise summary, so the Client doesn't need Jinja2 logic or file access.

## Static Asset Management

The user noted the need to handle documents _not_ in RAG (e.g., Character Sheets, Lore Docs).

### Server-Side Storage

These files reside in `~/.rag_dnd/campaigns/[id]/characters/` or `docs/`.

### Prompt Injection Strategy (Context Window)

Since modern LLMs (Gemini 1.5) have massive context windows (1M+ tokens), the simplest and most robust approach is **Server-Side Injection**.

1.  **Template Reference**: The `campaign.yaml` points to `characters/jams.md`.
2.  **Rendering**: When the Server renders `instructions.j2`, it detects these file references.
3.  **Injection**: Instead of leaving a path string (which the client can't read), the Server reads the file content and injects it into the prompt.
    - _Example System Prompt Output_:

      ```markdown
      # Player: Jams Capbarren

      [Start of Character Sheet: Jams]
      Name: Jams
      Class: Bard
      ...
      [End of Character Sheet]
      ```

### Alternative: Tool Retrieval (Optional)

For very large libraries of static docs (e.g., 50 PDFs), we can use a "Lazy Load" approach:

1.  **Indexing**: The Server indexes these descriptions in a light in-memory lookup or keywords.
2.  **Tool**: `read_campaign_asset(filename)` via API.
3.  **Prompt**: Lists available assets by name. "You have access to: `Map_of_Barovia`, `Letter_from_Strahd`."

> **Recommendation**: Start with **Injection** for Character Sheets and the Active Summary. Use **RAG** for everything else (old logs, dense lore books).

## Context Budget Analysis

The user specifically asked about the feasibility of injecting sheets for a party of 5-6 characters.

- **Model Capacity**: Gemini 1.5 Pro has a **2,000,000 token** context window.
- **Cost**:
  - Target System Prompt: ~5k tokens (Instruction)
  - Summary: ~5k-10k tokens
  - Character Sheet (Markdown): ~1k - 1.5k tokens each.
  - **Party of 6**: 6 \* 1.5k = **9k tokens**.
- **Total Impact**: ~24k tokens total. This is **~1.2%** of the available window.

**Conclusion**: For text/markdown character sheets, full injection is negligible and provides the best consistent character behavior.
**Optimization Plan**: If specific sheets become massive (e.g., full spell descriptions included), we can switch to a "Summary Sheet" for the prompt and allow RAG to retrieve specific spell details.
