# Implementation Plan: v0.4 Module Restructuring & Data Models

## Goal

Restructure the codebase to separate shared infrastructure from domain-specific modules, then implement all v0.4 Structured D&D Data models.

> [!IMPORTANT]
> **The user builds the code themselves.** This plan serves as a reference. The AI assistant provides advice and answers questions but does NOT make code changes.

---

## Phase 1: Module Restructuring & The Facade

Move shared infrastructure (`ORMBase`, `database.py`, `CampaignMetadata`) out of `rag/` into a new `core/` module. Break out the `Campaign` class into a top-level **Facade/Service** layer to orchestrate the modules.

### Target Structure

```
src/rag_dnd/
    campaign.py              # NEW FACADE — Moved from rag/campaign.py
    core/                    # NEW — shared infrastructure
        __init__.py          # exports: ORMBase, CampaignMetadata, get_session, init_db
        database.py          # MOVED from rag/database.py
        models.py            # ORMBase + CampaignMetadata (extracted from rag/models.py)
        exceptions.py        # RAGDNDException, CampaignNotFoundError
    rag/
        __init__.py          # UPDATE imports
        models.py            # KEEP: Collection, Document, Chunk, Sentence, QueryResult
        manager.py           # UPDATE imports
        store.py             # UPDATE imports
        embeddings.py        # UPDATE imports
        chunker.py           # UPDATE imports
        exceptions.py        # RAGException, DocumentNotFoundError
        llm.py               # unchanged
    game/                    # NEW — structured game data
        __init__.py
        enums.py             # All enums
        models.py            # Player, Character, Session, Turn, Asset + link tables
    server/                  # UPDATE imports
    client/                  # unchanged
    cli/                     # UPDATE imports to use the new top-level Campaign facade
    hooks/                   # unchanged
```

### Import Migration

| File | Old Import | New Import |
|---|---|---|
| `rag/models.py` | `from .database import get_session` | `from ..core.database import get_session` |
| `rag/manager.py` | `from .database import get_session` | `from ..core.database import get_session` |
| `rag/campaign.py` | `from .database import get_session` | `from ..core.database import get_session` |
| `rag/campaign.py` | `from .models import CampaignMetadata` | `from ..core.models import CampaignMetadata` |
| `rag/database.py` (old) | `from .models import ORMBase` | N/A — file moves to `core/` |
| `rag/__init__.py` | `from .database import init_db` | `from ..core.database import init_db` |
| `server/routes_v2.py` | `from .. import rag` | Kept, but `rag.init_db` now delegates to `core` |

### Steps

1. Create `src/rag_dnd/core/__init__.py`
2. Move `rag/database.py` → `core/database.py`, update its `ORMBase` import
3. Extract `ORMBase` + `CampaignMetadata` from `rag/models.py` → `core/models.py`
4. Update `core/database.py` to import `ORMBase` from `core.models`
5. Update all `rag/*.py` imports (see table above)
6. Keep `rag/models.py` with: `Collection`, `Document`, `Chunk`, `Sentence`, `QueryResult`
7. Add `from ..core.models import ORMBase` to `rag/models.py`
8. Update `rag/__init__.py` re-exports
9. Run server, verify nothing breaks

---

## Phase 2: Game Models

Create all 11 new models in `game/` using the [data_model.md](file:///C:/Users/tjans/.gemini/antigravity/brain/0862e5dc-c729-4fec-99d7-5c367a56629a/data_model.md) as reference.

### [NEW] `game/enums.py`

5 enums: `CharacterCategory`, `Disposition`, `RelationshipType`, `AssetType`, `PlayerType`.

### [NEW] `game/models.py`

All 11 models, importing `ORMBase` from `core.models`:

**Standalone:**
- `Player` (global, no campaign_id)
- `Character` (17 columns + JSON `data`)
- `Asset` (multimedia, filesystem reference)
- `Session` (with `session_number` + `summary`)
- `Turn`

**Link tables:**
- `PlayerCharacter` (player ↔ character ↔ session)
- `CharacterRelationship` (directional)
- `CharacterAsset` (M:N with `role`)
- `TurnCharacter` (M:N with `role`)
- `SessionAsset` (M:N with `context`)
- `ChunkCharacter` (entity-linking, imports `Chunk` from `rag.models`)

### Architectural Rule: Pragmatic Monolith
To prevent circular imports while retaining ORM magic:
1. **Never import `rag` models into `game` or vice versa.**
2. Use **string references** for relationships (e.g., `orm.relationship("Chunk")`).
3. Use **`backref`** from dependent models instead of explicitly declaring relationships in `core/` or across modules.

### Relationships to add in Phase 2
- `Game` models (`Character`, `Asset`, `Session`) should point to `CampaignMetadata` using schema:
  `campaign_id = mapped_column(ForeignKey("campaign_metadata.id"))`
  and dynamically inject the property into Core using backrefs:
  `campaign = relationship("CampaignMetadata", backref="characters")`

---

## Phase 3: Modify Existing Models (Without Circular Imports)

### [MODIFY] `core/models.py` — `CampaignMetadata`

Add the 3 state columns, but **DO NOT** add explicit relationships here to prevent `core` depending on `game`.

```python
current_location: Mapped[str | None]
current_date: Mapped[str | None]
active_session_id: Mapped[int | None]  # FK → sessions.id

# Do NOT define characters, assets or sessions here.
# These will be dynamically injected by backrefs in game/models.py.
```

### [MODIFY] `rag/models.py` — `Document` & `Chunk`

Add nullable FKs and string-based relationships to `Document`. Note the use of **string names** (`"Session"`, `"Asset"`) to avoid importing from `game.models`!

```python
session_id: Mapped[int | None] = mapped_column(ForeignKey("sessions.id"))
asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id"))
character_id: Mapped[int | None] = mapped_column(ForeignKey("characters.id"))

# Optional: ORM Magie via Strings
session = relationship("Session", backref="documents") 
asset = relationship("Asset", backref="documents")
character = relationship("Character", backref="documents")
```

For `Chunk` (`rag/models.py`):
```python
# To easily fetch the characters linked via ChunkCharacter M:N without circular imports
characters = relationship("Character", secondary="chunk_characters", backref="chunks")
```

---

## Phase 4: Verify

1. Start server: `uv run rag-server`
2. Verify `create_all()` creates all new tables
3. Check existing RAG functionality still works (query, ingest)
4. Inspect SQLite schema: `sqlite3 content.db ".tables"` and `.schema characters`

---

## Phased API/CLI Rollout (after models are stable)

| Phase | Scope |
|---|---|
| **4a** | Character + CharacterRelationship CRUD (API + CLI) |
| **4b** | Session + Turn endpoints (+ migrate transcript.py) |
| **4c** | Asset + link table endpoints |
| **4d** | Player + PlayerCharacter |
| **4e** | ChunkCharacter entity-linking (ingestion pipeline) |
| **4f** | CampaignMetadata state PATCH |
