# Functionele Eisen: Structured D&D Data (Fase 1)

> [!NOTE]
> Dit document is uitgewerkt in de [Gedetailleerde Karakter Specificatie](character_system_specification.md) en het [Geconsolideerde Ontwerp](character_system_detailed_design.md).


Dit document beschrijft de eisen voor de gestructureerde data-laag van `rag_dnd`. Deze laag vormt de basis voor de Prompt Engine en toekomstige game-mechanics.

## 1. Karakter Management

Het systeem moet informatie over verschillende soorten karakters kunnen opslaan:

- **Attributen:**
  - `name`: Unieke naam binnen de campagne (bijv. "Jams", "Buffy").
  - `category`: Type karakter (`PC` (Player Character), `NPC` (Non-Player Character), `PartyInfo`).
  - `description`: Markdown tekst met achtergrondinformatie ("Character Bible").
  - `is_active`: Status of het karakter momenteel deelneemt aan de sessie.
  - `portrait_url`: (Optioneel) Link naar een afbeelding.
- **Acties:**
  - Toevoegen, Wijzigen en Verwijderen van karakters via API en CLI.
  - Snel kunnen filteren op `is_active` en `category`.

## 2. Campaign State

Het systeem moet de actuele status van de campagne bijhouden:

- **Attributen:**
  - `current_location`: De naam van de huidige plek (bijv. "Phandalin", "Cragmaw Castle").
  - `current_date`: In-game datum en tijd (D&D kalender formaat).
  - `active_session_id`: Referentie naar de actieve sessie in de transcript-database.
- **Acties:**
  - Updaten van locatie en datum via API/CLI.
  - Ophalen van de volledige status voor gebruik in de Prompt Engine.

## 3. API Contract (v2)

### Karakter Beheer
- `GET /v2/campaigns/{short_name}/characters`: Lijst van alle karakters.
- `POST /v2/campaigns/{short_name}/characters`: Nieuw karakter toevoegen.
- `PUT /v2/campaigns/{short_name}/characters/{name}`: Karakter updaten.
- `DELETE /v2/campaigns/{short_name}/characters/{name}`: Karakter verwijderen.

### Campaign State
- `GET /v2/campaigns/{short_name}/state`: Huidige status ophalen.
- `PATCH /v2/campaigns/{short_name}/state`: Status gedeeltelijk updaten (locatie of datum).

## 4. CLI Integratie

- `rag-cli character list`: Overzicht van alle karakters.
- `rag-cli character add "<name>" --role NPC --desc "..."`: Toevoegen.
- `rag-cli character activate "<name>"`: Zet `is_active=True`.
- `rag-cli state set --location "Phandalin" --date "1491-03-23"`: Update state.
