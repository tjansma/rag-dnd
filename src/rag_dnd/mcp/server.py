"""Common MCP server for interacting with the RAG server."""
from fastmcp import FastMCP

from ..client import RAGClient, ClientConfig

rag_client = RAGClient(ClientConfig.load())

mcp = FastMCP("D&D RAG MCP Server")

@mcp.tool
def search_rag(query: str) -> str:
    """
    Search the RAG system for the given query.
    
    Args:
        query: The query to search for.
        
    Returns:
        str: The search results.
    """
    results = rag_client.query(query)
    
    answer = ""
    for result in results:
        answer += "---\n\nSOURCE DOCUMENT: " + result.source_document + "\n\n"
        answer += result.text
        answer += "\n\n"
    
    return answer

def main():
    mcp.run()

if __name__ == "__main__":
    main()
