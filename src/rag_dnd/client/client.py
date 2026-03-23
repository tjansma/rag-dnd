"""
Common client for interacting with the RAG server.
"""
import requests
from typing import List, Any
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


@dataclass
class CampaignResponse:
    id: int
    full_name: str
    short_name: str
    roleplay_system: str
    language: str
    active_summary_file: str | None
    session_log_file: str | None
    extensions: dict[str, Any] | None


class RAGClient:
    """Client for the RAG API."""
    
    def __init__(self, config: ClientConfig):
        """
        Initialize the RAG client.
        
        Args:
            config: The configuration for the RAG client.
        """
        self.config = config
        
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
            collection = self.config.collection

        url = f"{self.config.base_url}/v2/campaigns/{self.config.campaign}/documents"
        
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
        url = f"{self.config.base_url}/v2/campaigns/{self.config.campaign}/documents/{filename}"
        
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
        url = f"{self.config.base_url}/v2/campaigns/{self.config.campaign}/query"
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
        url = f"{self.config.base_url}/v2/llm/generate"
        payload = {"prompt": [{"role": "user", "content": query_text}]}
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        return response.json()

    def expand_query(self, session_guid: str, query: str) -> str | None:
        """
        Expand the query into a more specific search query.
        
        Args:
            session_guid (str): The GUID of the session.
            query (str): The query to expand.
        
        Returns:
            str | None: The expanded query, or None if not found.
        """
        url = f"{self.config.base_url}/v2/llm/expand_query"
        session_id = get_or_create_session(session_guid)
        last_turn = get_last_turn(session_id)
        if last_turn is None:
            return None

        extra_context = last_turn["ai_response"]
        payload = {"query": query, "extra_context": extra_context}
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        return response.json()

    def list_campaigns(self) -> List[CampaignResponse]:
        """
        List all campaigns.
        
        Returns:
            List[CampaignResponse]: The list of campaigns.
            
        Raises:
            requests.HTTPError: If the request fails.
        """
        url = f"{self.config.base_url}/v2/campaigns"
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        return [CampaignResponse(**item) for item in data]

    def create_campaign(self, full_name: str, short_name: str, roleplay_system: str, language: str, active_summary_file: str | None = None, session_log_file: str | None = None, extensions: dict[str, Any] | None = None) -> CampaignResponse:
        """
        Create a new campaign.
        
        Args:
            full_name (str): The full name of the campaign.
            short_name (str): The short name of the campaign.
            roleplay_system (str): The roleplay system of the campaign.
            language (str): The language of the campaign.
            active_summary_file (str | None): The active summary file of the campaign.
            session_log_file (str | None): The session log file of the campaign.
            extensions (list[str] | None): The extensions of the campaign.
            
        Returns:
            CampaignResponse: The created campaign.
            
        Raises:
            requests.HTTPError: If the request fails.
        """
        url = f"{self.config.base_url}/v2/campaigns"
        payload = {
            "full_name": full_name,
            "short_name": short_name,
            "roleplay_system": roleplay_system,
            "language": language,
            "active_summary_file": active_summary_file,
            "session_log_file": session_log_file,
            "extensions": extensions
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        return CampaignResponse(**response.json())

    def create_campaign_directory_structure(self) -> bool:
        """
        Create directory structure for campaign.
        
        Returns:
            bool: True if the directory structure was created successfully, False otherwise.
        """
        try:
            # By requesting these 3 properties, 'ClientConfig._resolve_path()' is called
            # under the hood, which safely creates the correct parent folders!
            _ = self.config.transcript_database
            _ = self.config.logbook_path
            _ = self.config.summary_prompt_file
            return True
        except OSError:
            return False
