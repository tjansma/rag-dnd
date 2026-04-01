# Implementation Plan: v0.4 Module Restructuring & Data Models

## Goal

Restructure the codebase to separate shared infrastructure from domain-specific modules, then implement all v0.4 Structured D&D Data models.

> [!IMPORTANT]
> **The user builds the code themselves.** This plan serves as a reference. The AI assistant provides advice and answers questions but does NOT make code changes.

---

## [✓ COMPLETED] Phase 1: Module Restructuring & The Facade

Move shared infrastructure (`ORMBase`, `database.py`, `CampaignMetadata`) out of `rag/` into a new `core/` module. Break out the `Campaign` class into a top-level **Facade/Service** layer to orchestrate the modules.

*(Volledig gerealiseerd. Imports zijn succesvol overgezet en `Campaign` fungeert nu als toplevel facade.)*

---

## [✓ COMPLETED] Phase 2: Game Models

Create all 11 new models in `game/` using the [data_model.md](v04_data_model.md) as reference.

### `game/enums.py`
Geïmplementeerd: `CharacterType`, `Disposition`, `RelationshipType`, `AssetType`, `PlayerType`.

### `game/models.py`
Alle modellen succesvol geïmplementeerd. 

> [!TIP]
> **Architectural Change (Pragmatic Monolith):**
> 1. Er worden NOOIT `rag` modellen in `game` of vice versa geïmporteerd (tenzij beschermd door `if TYPE_CHECKING`).
> 2. Circular imports worden voorkomen door string references (`orm.relationship("Chunk")`).
> 3. Entiteiten worden gekoppeld via backrefs en intersection tables.
> 4. `Asset` is losgekoppeld in een Global Asset Library, in plaats van campaign-bound.

---

## [✓ COMPLETED] Phase 3: Modify Existing Models (Integration)

In plaats van de oorspronkelijk geplande "Nullable Foreign Keys" in `RAGDocument` (wat leidt tot *sparse tables*), zijn we geweken naar een **strikte 3NF normalisatie**.

### `core/models.py` — `CampaignMetadata`
Toegevoegd:
```python
current_ingame_date: orm.Mapped[str | None]
latest_session_id: orm.Mapped[int | None]  # FK → game_sessions.id
```
*(Locatie is specifiek overgelaten aan GameCharacter.location wegens party-splits).*

### `rag/models.py` — RAGDocument & Chunk
Drie nieuwe **Junction Tables** (Koppeltabellen) gecreëerd om RAG documenten en game entiteiten veilig aan elkaar te linken:
1. `GameCharacterRAGDocument`
2. `GameSessionRAGDocument`
3. `AssetRAGDocument`

De backrefs zijn gedefinieerd als `_links`. Voorbeeld: `jams.rag_document_links`.

---

## [✓ COMPLETED] Phase 4: Verify

1. Server startup en schemageneratie is geverifieerd via `uv run rag-server`. Geen AmbiguousForeignKeys genoteerd na fix in Phase 3.
2. Alle tabellen succesvol geregistreerd in `content.db` (Bevestigd via SQLite Viewer in VS Code!).
3. RAG systeem (PUT bestanden) functioneert nog steeds!

---

## [IN PROGRESS] Phase 5: Phased API/CLI Rollout

| Phase | Status | Scope |
|---|---|---|
| **5a** | ⏳ TODO | Character + CharacterRelationship CRUD (API + CLI) |
| **5b** | ⏳ TODO | Session + Turn endpoints (+ migrate transcript.py) |
| **5c** | ⏳ TODO | Asset + link table endpoints |
| **5d** | ⏳ TODO | Player + PlayerCharacter |
| **5e** | ⏳ TODO | ChunkCharacter entity-linking (ingestion pipeline) |
| **5f** | ⏳ TODO | CampaignMetadata state PATCH |
| **5g** | ⏳ TODO | Prompt Engine (Server-side rendering character traits in system prompts) |
