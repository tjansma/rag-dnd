"""CLI tool for interacting with the RAG server."""
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
import os
from typing import Optional
import sys

from ..client import RAGClient, list_sessions, get_session_transcript, \
    session_to_markdown, ClientConfig, transcript_summarize

if os.name == 'nt':
    sys.stdin.reconfigure(encoding='utf-8')     # pyrefly: ignore
    sys.stdout.reconfigure(encoding='utf-8')    # pyrefly: ignore

app = typer.Typer(help="D&D RAG CLI Management Tool",
                  rich_help_panel="D&D RAG CLI Management Tool",
                  no_args_is_help=True)
llm_app = typer.Typer(help="Manage LLM", no_args_is_help=True)
rag_app = typer.Typer(help="Manage RAG knowledge base", no_args_is_help=True)
session_app = typer.Typer(help="Manage session transcripts", no_args_is_help=True)
campaign_app = typer.Typer(help="Manage campaigns", no_args_is_help=True)

app.add_typer(llm_app, name="llm")
app.add_typer(rag_app, name="rag")
app.add_typer(session_app, name="session")
app.add_typer(campaign_app, name="campaign")

console = Console()

# ------------------------------------------------------------------
# Lazy client initialization
# ------------------------------------------------------------------
# The client cannot be created at module level because the --campaign
# flag may override the config. We defer creation until first use.
# ------------------------------------------------------------------
_client: RAGClient | None = None
_campaign_override: str | None = None


def _get_client() -> RAGClient:
    """Get or create the RAG client, applying any --campaign override."""
    global _client
    if _client is None:
        overrides = {}
        if _campaign_override:
            overrides["campaign"] = _campaign_override
        config = ClientConfig.load(overrides=overrides if overrides else None)
        _client = RAGClient(config)
    return _client


@app.callback()
def main_callback(
    campaign: Optional[str] = typer.Option(
        None, "--campaign", "-c",
        help="Override the campaign short name from config."
    )
):
    """D&D RAG CLI Management Tool."""
    global _campaign_override
    if campaign:
        _campaign_override = campaign


# ==================================================================
# RAG commands
# ==================================================================

@rag_app.command()
def search(query: str, limit: int = 5):
    """
    Search the RAG knowledge base.

    Args:
        query (str): The search query.
        limit (int, optional): The number of results to return. Defaults to 5.
    
    Returns:
        None
    """
    try:
        client = _get_client()
        results = client.query(query, limit=limit)
        
        table = Table(title=f"Search Results for: '{query}'")
        table.add_column("Source", style="cyan", no_wrap=True)
        table.add_column("Excerpt", style="magenta")
        
        for res in results:
            # Truncate text for display
            display_text = res.text[:1000] + "..." if len(res.text) > 1000 else res.text
            display_text = display_text.replace("\n", " ")
            table.add_row(str(Path(res.source_document).name), display_text)
            
        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@rag_app.command()
def upload(file_path: str, collection: str | None = None):
    """
    Upload (store or update) a document in the campaign index.
    
    Args:
        file_path (str): The path to the document to upload.
        collection (str | None): The collection to upload the document to.
    
    Returns:
        None
    """
    try:
        client = _get_client()
        abs_path = os.path.abspath(file_path)
        console.print(f"Uploading document: [green]{abs_path}[/green]")
        client.store_document(abs_path, collection=collection)
        console.print("[bold green]Success![/bold green] Document stored.")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@rag_app.command()
def remove(filename: str, collection: str | None = None):
    """
    Remove a document from the campaign index.

    Args:
        filename (str): The filename of the document to remove.
        collection (str | None): The collection to remove the document from.

    Returns:
        None
    """
    try:
        client = _get_client()
        console.print(f"Removing document: [red]{filename}[/red]")
        client.delete_document(filename, collection=collection)
        console.print("[bold green]Success![/bold green] Document removed.")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


# ==================================================================
# Session commands
# ==================================================================

@session_app.command("list")
def session_list():
    """
    List all sessions.

    Returns:
        None
    """
    try:
        sessions = list_sessions()
        
        table = Table(title="Sessions")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("GUID", style="magenta")
        table.add_column("First Seen", style="green")
        
        for session in sessions:
            table.add_row(str(session["id"]), session["guid"], session["first_seen"])
            
        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

@session_app.command("show")
def session_show(id: int):
    """
    Show transcript of specific session.

    Args:
        id (int): The ID of the session.

    Returns:
        None
    """
    try:
        transcript = get_session_transcript(id)
        
        table = Table(title=f"Session {id} Transcript")
        table.padding = 1
        table.add_column("Player", style="cyan")
        table.add_column("DM", style="magenta")
        
        for turn in transcript:
            table.add_row(turn["user_prompt"], turn["ai_response"])
            
        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

@session_app.command("export")
def session_export(id: int, output_file: Optional[str]=None):
    """
    Export transcript of specific session.

    Args:
        id (int): The ID of the session.

    Returns:
        None
    """
    if not output_file:
        dest_file = sys.stdout
    else:
        dest_file = open(output_file, "w")

    dest_file.write(session_to_markdown(id))

    if output_file:
        dest_file.close()

@session_app.command("summarize")
def session_summarize(id: int, 
                      prompt_file: str | None = None, 
                      output: Optional[str] =  None, 
                      append: bool = False):
    """
    Generate a summary for a session using the Gemini CLI.

    Args:
        id (int): The ID of the session.
        prompt_file (str, optional): The path to the summary prompt file. Defaults to ClientConfig.summary_prompt_file.
        output (Optional[str], optional): The path to the output file. Defaults to None.
        append (bool, optional): Whether to append to the output file. Defaults to False.

    Returns:
        None
    """
    try:
        if prompt_file is None:
            prompt_file = ClientConfig.load().summary_prompt_file
        summary = transcript_summarize(id, prompt_file, output, append)
        console.print(summary)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


# ==================================================================
# LLM commands
# ==================================================================

@llm_app.command("chat")
def llm_chat(prompt: str):
    """
    Chat with the LLM.

    Args:
        prompt (str): The prompt to send to the LLM.

    Returns:
        None
    """
    try:
        client = _get_client()
        response = client.chat(prompt)
        console.print(response)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

@llm_app.command("expand_query")
def llm_expand_query(session_guid: str, query: str):
    """
    Expand the query into a more specific search query.
    
    Args:
        session_guid (str): The GUID of the session.
        query (str): The query to expand.
    
    Returns:
        str | None: The expanded query, or None if not found.
    """
    try:
        client = _get_client()
        expanded_query = client.expand_query(session_guid, query)
        console.print(expanded_query)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

if __name__ == "__main__":
    try:
        app()
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

# ==================================================================
# Campaign commands
# ==================================================================

@campaign_app.command("list")
def campaign_list():
    """
    List all campaigns.

    Returns:
        None
    """
    try:
        client = _get_client()
        campaigns = client.list_campaigns()
        
        table = Table(title="Campaigns")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Full Name", style="magenta")
        table.add_column("Short Name", style="green")
        
        for campaign in campaigns:
            table.add_row(str(campaign.id), campaign.full_name, campaign.short_name)
            
        console.print(table)
        console.print(f"\n[bold]Active campaign:[/bold] [green]{client.config.campaign}[/green]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

import json

@campaign_app.command("create")
def campaign_create(full_name: str, short_name: str, roleplay_system: str, language: str, active_summary_file: str | None = None, session_log_file: str | None = None, extensions: str | None = typer.Option(None, help="JSON string representing extensions")):
    """
    Create a new campaign.

    Args:
        full_name (str): The full name of the campaign.
        short_name (str): The short name of the campaign.
        roleplay_system (str): The roleplay system of the campaign.
        language (str): The language of the campaign.
        active_summary_file (str | None): The active summary file of the campaign.
        session_log_file (str | None): The session log file of the campaign.
        extensions (str | None): Valid JSON string of extensions.

    Returns:
        None
    """
    try:
        parsed_ext = None
        if extensions:
            parsed_ext = json.loads(extensions)
            
        client = _get_client()
        campaign = client.create_campaign(full_name, short_name, roleplay_system, language, active_summary_file, session_log_file, parsed_ext)
        console.print(f"[bold green]Success![/bold green] Campaign created: {campaign.full_name}")
        response = console.input(f"[yellow]Write active configuration to '{client.config.config_dir}/config.toml' to make this campaign active (y/n)?[/yellow]")
        if response.lower() == "y":
            client.config._campaign = short_name
            client.config.save_active_campaign()
            console.print(f"[bold green]Success![/bold green] Campaign set as active.")

            response = console.input(f"[yellow]Create directory structure for campaign (y/n)?[/yellow]")
            if response.lower() == "y":
                if client.create_campaign_directory_structure():
                    console.print(f"[bold green]Success![/bold green] Directory structure created.")
                else:
                    console.print(f"[bold red]Error:[/bold red] Could not create directory structure.")
    except json.JSONDecodeError:
        console.print("[bold red]Error:[/bold red] Extensions must be a valid JSON string.")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

@campaign_app.command("activate")
def campaign_activate(short_name: str):
    """
    Activate a campaign.

    Args:
        short_name (str): The short name of the campaign.

    Returns:
        None
    """
    try:
        client = _get_client()
        campaigns = client.list_campaigns()
        if short_name not in [c.short_name for c in campaigns]:
            console.print(f"[bold red]Error:[/bold red] Campaign {short_name} not found.")
            return

        client.config._campaign = short_name
        client.config.save_active_campaign()
        console.print(f"[bold green]Success![/bold green] Campaign set as active.")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")