"""
Common client for interacting with the RAG server.
"""
import requests
from typing import List
from dataclasses import dataclass, asdict

from .config import ClientConfig
from .transcript import get_or_create_session, get_last_turn


@dataclass
class QueryRequest:
    query: str
    max_results: int = 5
    collection_name: str | None = None


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
        self.campaign = config.campaign
        self.collection = config.collection
        
    def store_document(self, file_path: str, collection: str | None = None) -> None:
        """
        Store a document in the RAG system.
        
        Args:
            file_path (str): The absolute path to the document to store.
            collection (str | None): The collection to store the document in.
                                     Optional. If not provided, the campaign's
                                     default collection will be used.
            
        Raises:
            requests.HTTPError: If the request fails.
        """        
        if collection is None:
            collection = self.collection

        url = f"{self.base_url}/v2/campaigns/{self.campaign}/documents"
        
        params = {}
        if collection:
            params["collection_name"] = collection

        with open(file_path, "rb") as file_handle:
            file_stream = {"file": file_handle}
            response = requests.put(url, files=file_stream, params=params)

        response.raise_for_status()

    def delete_document(self, filename: str, collection: str | None = None) -> None:
        """
        Delete a document from the RAG system.
        
        Args:
            filename (str): The name of the document to delete.
            collection (str | None): The collection to delete the document from.
                                     Optional. If not provided, the campaign's
                                     default collection will be used.
            
        Raises:
            requests.HTTPError: If the request fails.
        """
        url = f"{self.base_url}/v2/campaigns/{self.campaign}/documents/{filename}"
        
        params = {}
        if collection:
            params["collection_name"] = collection

        response = requests.delete(url, params=params)
        response.raise_for_status()

    def query(self, query_text: str, limit: int = 5, collection: str | None = None) -> List[QueryResult]:
        """
        Query the RAG system.
        
        Args:
            query_text (str): The query text.
            limit (int): The maximum number of results to return.
            collection (str | None): The collection to query.
                                     Optional. If not provided, the campaign's
                                     default collection will be used.
            
        Returns:
            List[QueryResult]: The list of query results.
            
        Raises:
            requests.HTTPError: If the request fails.
        """
        url = f"{self.base_url}/v2/campaigns/{self.campaign}/query"
        query_request = QueryRequest(query=query_text,
                                     max_results=limit,
                                     collection_name=collection)
        response = requests.post(url, json=asdict(query_request))
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
        url = f"{self.base_url}/v2/llm/generate"
        payload = {"prompt": [{"role": "user", "content": query_text}]}
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
        url = f"{self.base_url}/v2/llm/expand_query"
        session_id = get_or_create_session(session_guid)
        last_turn = get_last_turn(session_id)
        if last_turn is None:
            return None

        extra_context = last_turn["ai_response"]
        payload = {"query": query, "extra_context": extra_context}
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        return response.json()
