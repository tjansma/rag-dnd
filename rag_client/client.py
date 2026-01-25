"""
Common client for interacting with the RAG server.
"""
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from client_config import ClientConfig

@dataclass
class QueryResult:
    text: str
    source_document: str

class RAGClient:
    """Client for the RAG API."""
    
    def __init__(self, config: ClientConfig):
        """
        Initialize the RAG client.
        
        Args:
            config: The configuration for the RAG client.
        """
        self.base_url = config.base_url.rstrip("/")
        
    def store_document(self, file_path: str) -> None:
        """
        Store a document in the RAG system.
        
        Args:
            file_path: The absolute path to the document to store.
            
        Raises:
            requests.HTTPError: If the request fails.
        """
        url = f"{self.base_url}/document"
        payload = {"file_path": file_path}
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
    def update_document(self, file_path: str) -> None:
        """
        Update an existing document in the RAG system.
        
        Args:
            file_path: The absolute path to the document to update.
            
        Raises:
            requests.HTTPError: If the request fails.
        """
        url = f"{self.base_url}/document"
        payload = {"file_path": file_path}
        response = requests.put(url, json=payload)
        response.raise_for_status()
        
    def delete_document(self, file_path: str) -> None:
        """
        Delete a document from the RAG system.
        
        Args:
            file_path: The absolute path to the document to delete.
            
        Raises:
            requests.HTTPError: If the request fails.
        """
        url = f"{self.base_url}/document"
        payload = {"file_path": file_path}
        # DELETE requests with body are allowed but sometimes tricky. 
        # Requests allows verify json kwarg.
        response = requests.request("DELETE", url, json=payload)
        response.raise_for_status()

    def query(self, query_text: str, limit: int = 5) -> List[QueryResult]:
        """
        Query the RAG system.
        
        Args:
            query_text: The query text.
            limit: The maximum number of results to return.
            
        Returns:
            List[QueryResult]: The list of query results.
            
        Raises:
            requests.HTTPError: If the request fails.
        """
        url = f"{self.base_url}/rag_query"
        payload = {"query": query_text, "limit": limit}
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        return [QueryResult(**item) for item in data]

    def chat(self, query_text: str) -> str:
        """
        Chat with the RAG system.
        
        Args:
            query_text: The query text.
            
        Returns:
            str: The response from the RAG system.
            
        Raises:
            requests.HTTPError: If the request fails.
        """
        url = f"{self.base_url}/llm_generate"
        payload = [{"role": "user", "content": query_text}]
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        return response.json()
