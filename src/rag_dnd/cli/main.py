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

app.add_typer(llm_app, name="llm")
app.add_typer(rag_app, name="rag")
app.add_typer(session_app, name="session")

console = Console()
client = RAGClient(ClientConfig.load())

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
def add(file_path: str):
    """
    Add a document to the index.
    
    Args:
        file_path (str): The path to the document to add.
    
    Returns:
        None
    """
    try:
        abs_path = os.path.abspath(file_path)
        console.print(f"Adding document: [green]{abs_path}[/green]")
        client.store_document(abs_path)
        console.print("[bold green]Success![/bold green] Document added.")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

@rag_app.command()
def upload(file_path: str, collection: str | None = None):
    """
    Upload a document to the index.
    
    Args:
        file_path (str): The path to the document to upload.
        collection (str | None): The collection to upload the document to.
    
    Returns:
        None
    """
    try:
        abs_path = os.path.abspath(file_path)
        console.print(f"Uploading document: [green]{abs_path}[/green]")
        status_code = client.store_document_v2(abs_path, collection)
        if status_code == 201:
            console.print("[bold green]Success![/bold green] New document added.")
        elif status_code == 200:
            console.print("[bold yellow]Success![/bold yellow] Existing document updated.")
        else:
            console.print(f"[bold red]Error:[/bold red] Unexpected status code: {status_code}")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

@rag_app.command()
def update(file_path: str):
    """
    Update an existing document.

    Args:
        file_path (str): The path to the document to update.
    
    Returns:
        None
    """
    try:
        abs_path = os.path.abspath(file_path)
        console.print(f"Updating document: [yellow]{abs_path}[/yellow]")
        client.update_document(abs_path)
        console.print("[bold green]Success![/bold green] Document updated.")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

@rag_app.command()
def remove(file_path: str):
    """
    Remove a document from the index.

    Args:
        file_path (str): The path to the document to remove.

    Returns:
        None
    """
    try:
        abs_path = os.path.abspath(file_path)
        console.print(f"Removing document: [red]{abs_path}[/red]")
        client.delete_document(abs_path)
        console.print("[bold green]Success![/bold green] Document removed.")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

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
                      prompt_file: str = ClientConfig.load().summary_prompt_file, 
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
        summary = transcript_summarize(id, prompt_file, output, append)
        console.print(summary)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

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
        expanded_query = client.expand_query(session_guid, query)
        console.print(expanded_query)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

if __name__ == "__main__":
    app()
