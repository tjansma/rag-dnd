"""
Common client for interacting with the RAG server.
"""
from rag_client.transcript import get_or_create_session
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from client_config import ClientConfig

from .transcript import get_last_turn

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

    def expand_query(self, session_guid: str, query: str) -> str | None:
        """
        Expand the query into a more specific search query.
        
        Args:
            session_id (int): The ID of the session.
            query (str): The query to expand.
        
        Returns:
            str | None: The expanded query, or None if not found.
        """
        url = f"{self.base_url}/expand_query"
        session_id = get_or_create_session(session_guid)
        last_turn = get_last_turn(session_id)
        if last_turn is None:
            return None

        extra_context = last_turn["ai_response"]
        payload = {"query": query, "extra_context": extra_context}
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        return response.json()
