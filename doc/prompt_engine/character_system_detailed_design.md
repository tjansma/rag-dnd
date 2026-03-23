# Ontwerpdocument: Unified Prompt & Character System

Dit document is gebaseerd op de [Prompt Engine Requirements](prompt_engine_requirements.md) en de [Structured Data Requirements](structured_data_requirements.md).


Dit document beschrijft de uitgebreide architectuur voor het beheer van gestructureerde D&D data en de dynamische generatie van AI-prompts in `rag-dnd`.

## 1. Overkoepelende Architectuur

Het systeem rust op drie complementaire lagen die samen de uiteindelijke instructie voor het LLM vormen:

1.  **RAG Layer (The Memory):** Haalt verhalende context (Lore) op uit Markdown sessie-logs middels hybride search.
2.  **Structured Data Layer (The Actors):** Beheert technische en persona gegevens van karakters (PC's, NPC's) en de actuele campagne-status (locatie, datum).
3.  **Prompt Engine (The Orchestrator):** Fungeert als de 'manager' die gegevens uit beide bronnen verzamelt en middels templates omzet in een coherente system-instruction.

---

## 2. Structured Data Layer

### Karakter Categorieën
| Categorie | Besturing | Gebruik |
| :--- | :--- | :--- |
| **PC** | Mens (Speler) | Referentie voor de AI zodat deze weet wie de speler is. |
| **PARTY_MEMBER** | AI | Volledig groepslid met stats en diepe persona. |
| **NPC** | AI | Belangrijke personages in de wereld, focus op persona. |
| **PASSERBY** | AI | Voorbijgangers met minimale data (slechts een 'vibe'). |
| **MONSTER** | AI/DM | Focus op combat statblock (AC, HP, Attacks). |

### Data Model
Data wordt opgeslagen in een hybride model in SQLite:
-   **Vaste Velden:** `id`, `name`, `category`, `is_active`.
-   **Flexible JSON (`data`):** Slaat alle systeem-specifieke stats op.
    -   **Source Data:** Basiswaarden (bijv. Strength 16, HP Max 24).
    -   **Persona:** Traits, Ideals, Bonds, Flaws.
    -   **Modifiers:** Actieve tijdelijke aanpassingen (bijv. +2 AC door 'Shield').

---

## 3. System Handlers & Modulairiteit

Om het systeem flexibel te houden voor andere RPG's (Cyberpunk, etc.), gebruiken we het **Handler Pattern**:

-   **Core Interface:** De applicatie-core beheert alleen de ruwe data.
-   **DnD5eHandler:** Een specifieke module die de ruwe JSON-data 'begrijpt' en berekent in **Derived Data** (bijv. Strength 16 -> Mod +3).
-   **System Registry:** Kiest op basis van de campaign settings automatisch de juiste handler.

---

## 4. Prompt Engine

De Prompt Engine transformeert data naar taal middels **Jinja2 templates**.

### Rollen & Templates
Templates worden geladen in een hiërarchie:
1.  `~/.rag_dnd/campaigns/{slug}/prompts/{role}.jinja2`
2.  Fallback: Globale standaard templates.

### AI-Triggers
De engine kan dynamische triggers bevatten:
-   *HP < 25%* -> Voeg persona trait 'Desperation' toe.
-   *Condition: Poisoned* -> Voeg instructie toe om misselijkheid te beschrijven.

---

## 5. Integratie Workflow

Wanneer een prompt wordt verwerkt:
1.  **Identificatie:** De Prompt Engine bepaalt de actieve rol (bijv. `dm` of `party`).
2.  **Data Fetching:**
    -   RAG zoekt naar relevante lore.
    -   Structured Data haalt de `is_active` karakters op.
3.  **Enrichment:** De System Handler berekent alle derived stats.
4.  **Synthesis:** De Jinja2 template voegt alles samen:
    > "Jij bent de DM. De party is in Phandalin (Lore). Buffy heeft 10/20 HP en voelt zich zwak (Stats/Triggers). Jams is de speler."
5.  **Output:** De verrijkte instructie gaat naar Gemini.

---

## 6. Technische Roadmap

-   **Fase 1:** Implementatie van `Character` en `CampaignState` modellen in SQLAlchemy en v2 API.
-   **Fase 2:** Bouwen van de `PromptEngine` en de `DnD5eHandler`.
-   **Fase 3:** Integratie in de Gemini CLI Hook en de MCP Server.
