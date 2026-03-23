# Functionele Eisen: Prompt Engine

> [!NOTE]
> Voor de volledige architectuur en de integratie met Karakter-data, zie het [Geconsolideerde Ontwerpdocument](character_system_detailed_design.md).
 (v1.0)

De **Prompt Engine** is verantwoordelijk voor het samenstellen van de "System Instruction" of "System Prompt" die naar het LLM wordt gestuurd. Het combineert statische templates met dynamische data uit de RAG-database en andere bronnen.

## 1. Persona Beheer (Templates)

- **Rollen:** De engine moet verschillende rollen ondersteunen:
  - `dm`: De standaard Dungeon Master persona.
  - `lore_keeper`: Een neutrale rol die focus legt op feitelijke consistentie.
  - `npc`: Een basis-persona voor niet-speler karakters.
  - `npc:{name}`: Specifieke persona's voor belangrijke NPC's (bijv. `npc:nezznar`).
  - `party`: Een gecombineerde persona voor scenario's waarin het LLM de DM én de hele party (behalve de speler) bestuurt.
- **Opslag:** Templates worden opgeslagen als `.jinja2` of `.txt` bestanden op de server.
- **Hiërarchie:** 
  1. Campaign-specifieke templates (bijv. `~/.rag_dnd/campaigns/{slug}/prompts/dm.jinja2`).
  2. Global fallback templates (bijv. `src/rag_dnd/prompts/default/dm.jinja2`).

## 2. Dynamische Variabelen (Injectie)

De engine moet de volgende variabelen kunnen injecteren in de templates:

- `{{ lore }}`: De gerelateerde "chunks" die uit de RAG-query komen, geformatteerd met headers (bijv. "Source: Session 5").
- `{{ session_summary }}`: Een samenvatting van de huidige of voorgaande sessies.
- `{{ character_sheets }}`: Een lijst met achtergronden en karakteristieken voor alle actieve NPC's en partyleden (bijv. Buffy, Hermione, Lara).
- `{{ player_stats }}`: Informatie over de speler (Jams) zodat de AI weet wie hij *niet* is.
- `{{ current_relationships }}`: (Optioneel) Relatie-status tussen karakters (bijv. "Hermione is flustered by Jams' teasing").
- `{{ rules_reference }}`: (Optioneel/Toekomst) Specifieke regels die relevant zijn voor de huidige actie (bijv. "Grappling rules").

## 3. API Contract

### Render Prompt Endpoint
`POST /v2/campaigns/{short_name}/prompt/render`

**Input:**
```json
{
  "role": "dm",
  "query": "Wie is de zwarte spin?",
  "additional_context": {
    "location": "Cragmaw Castle",
    "active_npc": "Sildar Hallwinter"
  }
}
```

**Output:**
```json
{
  "rendered_system_instruction": "Jij bent een Dungeon Master... [Lore info over Nezznar]... Je bevindt je in Cragmaw Castle...",
  "meta": {
    "template_used": "campaign_custom_dm",
    "tokens_estimated": 450
  }
}
```

## 4. Configuratie Eisen

- **Context Window Management:** De engine moet een limiet kunnen stellen aan de hoeveelheid lore die wordt geïnjecteerd om te voorkomen dat de context-window van het model (of de token-kosten) ontploft.
- **Formatting:** De output moet altijd in schoon Markdown zijn, geoptimaliseerd voor LLM's (duidelijke scheiding tussen instructies en data).

## 5. Gebruikers-interface (CLI)

- `rag-cli prompt list`: Toon beschikbare roles/templates voor de actieve campagne.
- `rag-cli prompt test <role> "<query>"`: Test de rendering van een prompt zonder deze naar het LLM te sturen.

## 6. Integratie & Architectuur

### Gemini CLI Hook (`rag-hook-context`)
- **Huidige status:** Formatteert zelf de RAG-chunks in een hardcoded string.
- **Nieuwe workflow:**
  1. Leest `RAG_DND_ROLE` uit de omgeving (default: `dm`).
  2. Roept `POST /v2/campaigns/{short_name}/prompt/render` aan op de server.
  3. De server voert de RAG-search uit én rendert de template.
  4. De hook geeft de gerenderde tekst terug via de `systemInstruction` (of `additionalContext`) in de JSON response naar Gemini.

### MCP Server (`rag-mcp`)
- **Nieuwe tool:** `get_persona_prompt(role: str, query: str)`.
- **Functie:** Stelt een AI-agent (zoals in een IDE) in staat om direct een persona-specifieke instructie op te vragen voor een bepaalde context.
- **Voordeel:** De identiteit van de NPC of de DM zit centraal op de server, niet verspreid over verschillende clients.

### Server-side Logica
- De `PromptEngine` wordt een core component in `src/rag_dnd/core`.
- Het gebruikt de bestaande `VectorStore` en `Manager` om data op te halen.
- Het gebruikt `Jinja2` voor flexibele templates.

## 7. Data Schema Uitbreiding

Om deze functies te ondersteunen, moet de SQLite database worden uitgebreid met:

### Character Tabel
- `id`: Primary Key
- `campaign_id`: Foreign Key naar `CampaignMetadata`.
- `name`: Naam van het karakter (bijv. "Buffy", "Hermione").
- `role`: Type karakter (`player`, `npc`, `party_member`).
- `description`: De "Character Bible" tekst (Markdown).
- `is_active`: Boolean (is dit karakter momenteel aanwezig in de sessie?).

### Campaign State (Optioneel)
- `current_location`: Tekstveld voor de huidige plek.
- `current_date`: In-game datum.
- `active_session_id`: Referentie naar de lopende sessie in `transcript.db`.
