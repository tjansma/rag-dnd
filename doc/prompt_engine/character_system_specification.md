# Specificatie: D&D Karakter Systeem (v1.0)

> [!NOTE]
> Zie voor de overkoepelende architectuur het [Gedetailleerde Ontwerpdocument](character_system_detailed_design.md).


Dit document detailleert hoe we D&D karakters en hun eigenschappen opslaan om zowel de spelmechanica als de AI-persona's te ondersteunen.

## 1. Karakter Categorieën

We maken onderscheid in diepgang en besturing:

| Categorie | Besturing | Detailniveau | Gebruik in RAG/LLM |
| :--- | :--- | :--- | :--- |
| **PC** (Player Character) | Mens (Tim) | Hoog | Referentie voor de AI zodat deze weet wie de speler is en wat hij kan. |
| **PARTY_MEMBER** | LLM | Hoog | Volledige persona + stats. De AI speelt dit karakter als een volwaardig groepslid. |
| **NPC** | LLM | Medium | Belangrijke personages met een "Character Bible", maar minder focus op game-stats (tenzij combat). |
| **PASSERBY** | LLM | Laag | Voorbijgangers. Slechts een 'vibe' of één unieke eigenschap nodig. |
| **MONSTER** | LLM/DM | Medium (Combat) | Focus op de statblock (AC, HP, Attacks). |

## 2. Data Velden (Schema)

### Basis Velden (Kolommen)
- `id` (PK)
- `campaign_id` (FK)
- `name` (String, Unique per campaign)
- `category` (Enum: PC, PARTY_MEMBER, NPC, PASSERBY, MONSTER)
- `is_active` (Boolean: Aanwezig in huidige scene?)

### Gestructureerde Data (JSON Blob `data`)
We gebruiken het concept van **Source Data** (wat we opslaan) en **Derived Data** (wat de code berekent voor de prompt).

#### A. Source Data (Opgeslagen)
- **Identity:** `race`, `class`, `level`, `background`, `alignment`, `xp`.
- **Abilities (Base Scores):** `str`, `dex`, `con`, `int`, `wis`, `cha`.
- **Combat (Base):** `hp_max`, `ac_base`, `speed`, `initiative_bonus`.
- **Modifiers:** Een lijst met actieve aanpassingen:
  ```json
  [
    {"type": "bonus", "target": "ac", "value": 2, "source": "Shield", "active": true},
    {"type": "proficiency", "target": "stealth", "source": "Criminal Background"}
  ]
  ```
- **Resources & Spellcasting:**
  - `resources`: `{ "ki": 3, "sorcery_points": 5 }`
  - `spell_slots`: `{ "1": {"max": 4, "used": 1}, "2": {"max": 2, "used": 0} }`
- **Conditions:** `["Poisoned", "Prone"]`.
- **Inventory (Key Items):** Items die invloed hebben op stats of lore.

#### B. Current State (Lopende Sessie)
- `hp_current`, `hp_temp`.
- **Action Economy:** `{ "action": 1, "bonus_action": 1, "reaction": 1 }` (wordt gereset per ronde).
- **Inspiration:** Boolean.

#### C. Derived Data (Berekend door Engine)
De Engine combineert Source + Modifiers om de finale waarden voor de prompt te bepalen:
- `Final AC` = Base + Dex + Modifiers.
- `Skill Modifiers` = Ability Mod + (Proficiency ? Prof Bonus : 0) + Modifiers.

#### D. Persona & AI-Triggers (Cruciaal voor LLM)
- **Persona:** `traits`, `ideals`, `bonds`, `flaws`, `background_story`.
- **AI-Triggers:** Specifieke instructies gebaseerd op status:
  - *"If hp_current < 25%: Je bent paniekerig en meer geneigd om te vluchten."*
  - *"If condition contains 'Poisoned': Beschrijf hoe je misselijk bent in je acties."*
- `personality_traits`: "Maakt vaak ongepaste grappen in serieuze situaties."
- `ideals`: "Vrijheid: Iedereen moet zijn eigen pad kunnen kiezen."
- `bonds`: "Hermione: Ziet haar als een zus die bescherming nodig heeft."
- `flaws`: "Kan geen nee zeggen tegen een gokje."
- `background_story`: Langere tekst over de geschiedenis van het karakter.

## 3. Vertaling naar Prompt Context

De Prompt Engine vertaalt deze data naar een instructie:

**Voorbeeld voor Buffy (Party Member):**
> "Jij speelt Buffy. Je bent een Lawful Good Paladin (Human). 
> Je Personality Traits: [traits]. Jouw band met Jams: [bonds].
> Je hebt op dit moment 20/24 HP en je AC is 15. Gebruik deze informatie om je acties in de combat en roleplay realistisch te beschrijven."

## 5. Systeem-Onafhankelijkheid

Hoewel de focus nu op D&D 5e ligt, is het ontwerp modulair:

1. **Flexibele Data (`data` JSON):** Omdat we stats niet in vaste kolommen zetten, kun je morgen een Cyberpunk campaign starten met `REF`, `TECH` en `COOL` stats zonder code-wijzigingen.
2. **Systeem-specifieke Templates:** De `PromptEngine` gebruikt de `system` vlag van de campaign om de juiste templates te laden. Een Cyberpunk template weet dat hij naar `humanity` moet kijken in plaats van naar `spell_slots`.
3. **Ontkoppelde Logica:** De berekening van 'Derived Data' (zoals Modifiers) wordt per systeem gedefinieerd in een 'System Handler'. Voor D&D 5e bouwen we de eerste handler, maar de architectuur ondersteunt uitbreiding naar elk ander systeem.
 
## 6. Architectuur: Systeem Handlers

Om de 'Core' van de applicatie los te koppelen van de D&D-regels, gebruiken we het **Handler Pattern**:

### De Flow
1. **Source Data**: De `Character` tabel in SQLite bevat de ruwe JSON (bijv. `{ "str": 16 }`).
2. **Registry**: De `PromptEngine` vraagt de `SystemRegistry` om de handler die hoort bij de `system` vlag van de campaign (bijv. "dnd5e").
3. **Handler**: De `DnD5eHandler` krijgt de ruwe data en berekent de 'Derived Data' (bijv. `str_mod: +3`).
4. **Context**: De handler levert een verrijkt object aan de `PromptEngine`.
5. **Prompt**: De Jinja2 template gebruikt dit object om de uiteindelijke instructie te renderen.

### Waarom deze aanpak?
- **Core is stabiel**: De database en de server-code veranderen niet als we een nieuw spel-systeem toevoegen.
- **Handlers zijn lichtgewicht**: Een nieuwe handler is alleen een Python klasse die een interface implementeert.
- **Templates zijn flexibel**: De AI-instructies kunnen per systeem compleet anders zijn zonder de onderliggende logica te beïnvloeden.

## 7. Integratie met RAG-Module

De Structured Data en de RAG-module zijn complementair:

- **RAG (The Story)**: Levert de verhalende context ("Wat is er ook alweer gebeurd in die grot?").
- **Structured Data (The Actors)**: Levert de mechanische en persona context ("Wie ben ik en wat kan ik op dit moment?").

### De Koppeling
De `PromptEngine` combineert beide bronnen in één overkoepelende context:
1. **Input**: Gebruiker stelt een vraag ("Buffy, val de goblin aan!").
2. **RAG Search**: Haalt info op over goblins en de huidige locatie vanuit de Markdown logs.
3. **Structured Search**: Haalt Buffy's character-sheet en actuele HP/Spells op.
4. **Prompt Rendering**: Combineert Lore + Stats + Persona in de system-prompt voor Gemini.

Op deze manier 'weet' de AI niet alleen de feiten uit het verhaal, maar kan hij ze ook op de juiste manier (volgens de regels en het karakter) uitvoeren.


