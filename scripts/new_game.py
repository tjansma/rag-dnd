import chromadb.utils.embedding_functions.instructor_embedding_function
import jinja2
import jinja2.meta
from pathlib import Path
from dataclasses import dataclass

INSTRUCTION_PROMPT_TEMPLATE = Path("prompts/game/instructions.j2").resolve()

@dataclass
class Document:
    name: str
    description: str
    file: Path

@dataclass
class Character:
    name: str
    character_sheet_file: Path
    his_or_her: str
    he_or_she: str
    him_or_her: str
    his_or_hers: str


@dataclass
class Campaign:
    name: str | None = None
    summary_file: Path | None = None
    pc: Character | None = None
    party_members: list[Character] | None = None
    docs: list[Document] | None = None
    language: str | None = None

def main():
    campaign_name = input("Campaign name: ")
    pc_name = input("Player character name: ")

    campaign = Campaign(
        name=campaign_name,
        summary_file=Path(f"data/campaigns/{campaign_name}/summary.md"),
        pc=Character(
            name=pc_name,
            character_sheet_file=Path(f"data/campaigns/{campaign_name}/pc/{pc_name}.md"),
            his_or_her=input("His or her: "),
            he_or_she=input("He or she: "),
            him_or_her=input("Him or her: "),
            his_or_hers=input("His or hers: "),
        ),
        party_members=[],
        docs=[],
        language="",
    )

    while True:
        if input("Add a party member? (y/n): ").lower() == "n":
            break
            
        pm_name = input("Party member name: ")
        party_member = Character(
            name=pm_name,
            character_sheet_file=Path(f"data/campaigns/{campaign.name}/party_members/{pm_name}.md"),
            his_or_her=input("His or her: "),
            he_or_she=input("He or she: "),
            him_or_her=input("Him or her: "),
            his_or_hers=input("His or hers: "),
        )
        campaign.party_members.append(party_member)

    while True:
        if input("Add a document? (y/n): ").lower() == "n":
            break
            
        doc_name = input("Document name: ")
        doc = Document(
            name=doc_name,
            description=input("Document description: "),
            file=Path(f"data/campaigns/{campaign.name}/docs/{doc_name}.md"),
        )
        campaign.docs.append(doc)

    campaign.language = input("Language: ")
    
    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(INSTRUCTION_PROMPT_TEMPLATE.parent),
        autoescape=jinja2.select_autoescape(),
    )
    instruction_prompt = jinja_env.get_template(INSTRUCTION_PROMPT_TEMPLATE.name).render(campaign=campaign)
    print(instruction_prompt)

if __name__ == "__main__":
    main()