"""
CLI tool for interacting with the RAG server.
"""
from pathlib import Path
import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
import os
import sys

from rag_client import RAGClient
from client_config import ClientConfig

app = typer.Typer(help="D&D RAG CLI Management Tool")
console = Console()
client = RAGClient(ClientConfig())

@app.command()
def search(query: str, limit: int = 5):
    """
    Search the RAG knowledge base.
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

@app.command()
def add(file_path: str):
    """
    Add a document to the index.
    """
    try:
        abs_path = os.path.abspath(file_path)
        console.print(f"Adding document: [green]{abs_path}[/green]")
        client.store_document(abs_path)
        console.print("[bold green]Success![/bold green] Document added.")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

@app.command()
def update(file_path: str):
    """
    Update an existing document.
    """
    try:
        abs_path = os.path.abspath(file_path)
        console.print(f"Updating document: [yellow]{abs_path}[/yellow]")
        client.update_document(abs_path)
        console.print("[bold green]Success![/bold green] Document updated.")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

@app.command()
def remove(file_path: str):
    """
    Remove a document from the index.
    """
    try:
        abs_path = os.path.abspath(file_path)
        console.print(f"Removing document: [red]{abs_path}[/red]")
        client.delete_document(abs_path)
        console.print("[bold green]Success![/bold green] Document removed.")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

if __name__ == "__main__":
    app()
