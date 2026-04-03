"""
Common client for interacting with the RAG server.
"""
import requests
from typing import List, Any, Union

from .config import ClientConfig
from .transcript import get_or_create_session, get_last_turn
from .models import (
    CampaignResponse, 
    QueryRequest, 
    QueryResult,
    HumanPlayerCreate,
    AIPlayerCreate,
    HumanPlayerResponse,
    AIPlayerResponse
)

PlayerCreateType = Union[HumanPlayerCreate, AIPlayerCreate]
PlayerResponseType = Union[HumanPlayerResponse, AIPlayerResponse]


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
        response = requests.post(url, json=query_request.model_dump())
        response.raise_for_status()
        
        data = response.json()
        return [QueryResult.model_validate(item) for item in data]

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
        return [CampaignResponse.model_validate(item) for item in data]

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
        
        return CampaignResponse.model_validate(response.json())

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

    def get_players(self) -> List[PlayerResponseType]:
        """
        Get all players.
        
        Returns:
            List[PlayerResponseType]: The list of players.
        """
        url = f"{self.config.base_url}/v2/players"
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        results = []
        for item in data:
            if item.get("player_type") == "human":
                results.append(HumanPlayerResponse.model_validate(item))
            elif item.get("player_type") == "ai":
                results.append(AIPlayerResponse.model_validate(item))
        return results

    def get_player(self, player_id: int = None, player_name: str = None) -> PlayerResponseType:
        """
        Get a player by ID or name.
        
        If both player_id and player_name are provided, player_id will be used.
        At least one of player_id or player_name must be provided.
        
        Args:
            player_id (int): The ID of the player. (optional)
            player_name (str): The name of the player. (optional)
            
        Returns:
            PlayerResponseType: The player.
        """
        if player_id is None and player_name is None:
            raise ValueError("Either player_id or player_name must be provided.")
        if player_id is not None:
            url = f"{self.config.base_url}/v2/players/{player_id}"
        else:
            url = f"{self.config.base_url}/v2/players/name/{player_name}"
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        if data.get("player_type") == "human":
            return HumanPlayerResponse.model_validate(data)
        return AIPlayerResponse.model_validate(data)
        
    def register_player(self, player: PlayerCreateType) -> PlayerResponseType:
        """
        Register a new player.
        
        Args:
            player (PlayerCreateType): The player to register.
            
        Returns:
            PlayerResponseType: The registered player.
        """
        url = f"{self.config.base_url}/v2/players"
        response = requests.post(url, json=player.model_dump())
        response.raise_for_status()
        
        data = response.json()
        if data.get("player_type") == "human":
            return HumanPlayerResponse.model_validate(data)
        return AIPlayerResponse.model_validate(data)
