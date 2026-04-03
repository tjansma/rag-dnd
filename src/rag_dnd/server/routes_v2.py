"""FastAPI routes for API requests."""
import logging

from fastapi import APIRouter, UploadFile, HTTPException, Depends, Path
from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from .. import game
from .. import rag
from ..campaign import Campaign

from .dependencies import database_session, get_campaign_and_collection
from .upload import temporary_upload
from .schemas import QueryRequest, LLMMessage, ExpandQueryRequest, \
    CreateCampaignRequest, CampaignResponse

logger = logging.getLogger(__name__)

router_v2 = APIRouter(prefix="/v2")

# ===========================================================================
# Campaign routes
# ===========================================================================
# Campaign mutation routes
# ---------------------------------------------------------------------------

@router_v2.post("/campaigns", status_code=201)
def create_campaign(request: CreateCampaignRequest) -> CampaignResponse:
    """
    Create a new campaign.

    Args:
        request (CreateCampaignRequest): The request to create a new campaign.

    Returns:
        CampaignResponse: The created campaign.
    """
    campaign = Campaign.create(
        full_name=request.full_name,
        short_name=request.short_name,
        roleplay_system=request.roleplay_system,
        language=request.language,
        active_summary_file=request.active_summary_file,
        session_log_file=request.session_log_file,
        extensions=request.extensions
    )
    return CampaignResponse(
        id=campaign.metadata.id,
        full_name=campaign.metadata.full_name,
        short_name=campaign.metadata.short_name,
        roleplay_system=campaign.metadata.system,
        language=campaign.metadata.language,
        active_summary_file=campaign.metadata.active_summary_file,
        session_log_file=campaign.metadata.session_log_file,
        extensions=campaign.metadata.extensions
    )

# ---------------------------------------------------------------------------
# Campaign query routes
# ---------------------------------------------------------------------------

@router_v2.get("/campaigns")
def get_campaign_list() -> list[CampaignResponse]:
    """
    Get a list of all campaigns.

    Returns:
        list[CampaignResponse]: The list of campaigns.
    """
    campaigns = Campaign.list_all()
    return [CampaignResponse(
        id=campaign.metadata.id,
        full_name=campaign.metadata.full_name,
        short_name=campaign.metadata.short_name,
        roleplay_system=campaign.metadata.system,
        language=campaign.metadata.language,
        active_summary_file=campaign.metadata.active_summary_file,
        session_log_file=campaign.metadata.session_log_file,
        extensions=campaign.metadata.extensions
    ) for campaign in campaigns]


# ===========================================================================
# Document routes
# ===========================================================================
# Document mutation routes
# ---------------------------------------------------------------------------
@router_v2.put("/campaigns/{campaign_short_name}/documents", status_code=200)
def update_document(file: UploadFile,
                    campaign_and_collection: tuple[Campaign, str] = 
                        Depends(get_campaign_and_collection)
                   ):
    """
    Store or update a document in the database.
    
    Args:
        file (UploadFile): The file to update.
        campaign_short_name (str): The short name of the campaign to update
                                   the document in.
        collection_name (str | None): The name of the collection to update
                                     the document in.
    """
    campaign, collection_name = campaign_and_collection

    logger.debug(f"Updating document: {file.filename} in collection: "
                 f"{collection_name}")

    # Receive the file
    logger.debug(f"Updating document in database: {file.filename}")
    try:
        with temporary_upload(file) as file_path:
            try:
                campaign.store_document(file_path, 
                                        custom_filename=file.filename, 
                                        collection_name=collection_name)
            except FileNotFoundError as e:
                logger.error(f"Error updating document in database: {e}")
                raise HTTPException(status_code=404, 
                                    detail="Document does not exist on file "
                                           "system")
    except OSError as e:
        logger.error(f"Error updating document in database: {e}")
        raise HTTPException(status_code=500, 
                            detail="Internal server error")
    logger.info(f"Document updated in database: {file.filename}")

@router_v2.delete("/campaigns/{campaign_short_name}/documents/{filename}")
def delete_document(filename: str,
                    campaign_and_collection: tuple[Campaign, str] = 
                        Depends(get_campaign_and_collection)
                   ) -> None:
    """
    Delete a document from the database.
    
    Args:
        campaign_short_name (str): The short name of the campaign to delete
                                   the document from.
        filename (str): The name of the document to delete.
        collection_name (str | None): The name of the collection to delete
                                     the document from.
    """
    campaign, collection_name = campaign_and_collection

    logger.debug(f"routes_v2.delete_document: Deleting document: "
                 f"{filename} from collection: {collection_name}")
    try:
        campaign.delete_document(filename, collection_name=collection_name)
    except rag.DocumentNotFoundError as e:
        logger.error(f"routes_v2.delete_document: Error deleting document: {e}")
        raise HTTPException(status_code=404, detail="Document not found")
    except Exception as e:
        logger.error(f"routes_v2.delete_document: Error deleting document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    logger.info(f"routes_v2.delete_document: Document deleted from database: {filename}")

# ===========================================================================
# RAG query routes
# ===========================================================================
# Post query routes
# ---------------------------------------------------------------------------
@router_v2.post("/campaigns/{campaign_short_name}/query")
def query_campaign(request: QueryRequest,
                   campaign_and_collection: tuple[Campaign, str] = 
                        Depends(get_campaign_and_collection)
                   ) -> list[rag.QueryResult]:
    """
    Query the campaign RAG system.
    
    Args:
        request (QueryRequest): The query to ask.
        campaign_short_name (str): The short name of the campaign to query.
    """
    campaign, collection_name = campaign_and_collection

    # Als de body param een specifieke collection_name meestuurt, overschrijft
    # deze de default collection uit de dependency
    if request.collection_name is not None:
        collection_name = request.collection_name

    logger.debug(f"routes_v2.query_campaign: Entering "
                 f"campaign_short_name={campaign.metadata.short_name}, "
                 f"{request=}")
                 
    logger.debug(f"routes_v2.query_campaign: Querying campaign: "
                 f"{campaign.metadata.short_name} in collection: "
                 f"{collection_name}")
    try:
        result = campaign.query_rag(request.query, 
                                    collection_name=collection_name, 
                                    max_results=request.max_results)
    except ValueError as e:
        logger.error(f"routes_v2.query_campaign: Error querying campaign: {e}")
        raise HTTPException(status_code=404, detail="Collection not found")
    except Exception as e:
        logger.error(f"routes_v2.query_campaign: Error querying campaign: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    logger.info(f"routes_v2.query_campaign: "
                f"Campaign queried: {campaign.metadata.short_name}")
    return result


# ===========================================================================
# LLM routes
# ===========================================================================
# LLM generation routes
# ---------------------------------------------------------------------------
@router_v2.post("/llm/generate")
def llm_generate(prompt: list[LLMMessage]) -> str:
    """
    Generate text using the LLM.
    
    Args:
        prompt (list[LLMMessage]): The prompt to generate text from.
    """
    logger.debug(f"routes_v2.llm_generate: Entering {prompt=}")
    try:
        messages = [ { "role": message.role, "content": message.content } 
                    for message in prompt ]
        result = rag.prompt_llm(messages)
    except Exception as e:
        logger.error(f"routes_v2.llm_generate: Error generating text: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    logger.info(f"routes_v2.llm_generate: Text generated: {result}")
    return result


@router_v2.post("/llm/expand_query")
def llm_expand_query(request: ExpandQueryRequest) -> str:
    """
    Expand a query using the LLM.
    
    Args:
        request (ExpandQueryRequest): The request to expand the query.
    """
    logger.debug(f"routes_v2.llm_expand_query: Entering {request=}")
    try:
        result = rag.expand_query(request.query, request.extra_context)
    except Exception as e:
        logger.error(f"routes_v2.llm_expand_query: Error expanding query: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    logger.debug(f"routes_v2.llm_expand_query: Query expanded: {result}")
    return result

# ===========================================================================
# Player routes
# ===========================================================================
# Player mutation routes
# ---------------------------------------------------------------------------

@router_v2.post("/players", 
                response_model=game.PlayerResponseSchema, 
                status_code=201)
def register_player(request: game.PlayerCreateSchema, 
                    db_session: Session = Depends(database_session)) -> \
        game.PlayerResponseSchema:
    """
    Register a new player.
    
    Args:
        request (game.PlayerCreateSchema): The request to register a new player.
        db_session (Session): The database session.

    Returns:
        game.PlayerResponseSchema: The registered player.

    Raises:
        HTTPException: If the player already exists or an error occurs.
    """
    logger.debug(f"routes_v2.register_player: Entering {request=}")
    try:
        player = game.register_player(request, db_session)
        db_session.commit()
    except game.PlayerExistsError as e:
        logger.error(f"routes_v2.register_player: "
                     f"Error registering player: {e}")
        raise HTTPException(status_code=400, detail="Player already exists")
    except Exception as e:
        db_session.rollback()
        logger.error(f"routes_v2.register_player: "
                     f"Error registering player: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    logger.info(f"routes_v2.register_player: "
                f"Player registered: {player.name}")
    
    return TypeAdapter(game.PlayerResponseSchema).validate_python(player)

# ---------------------------------------------------------------------------
# Player query routes
# ---------------------------------------------------------------------------
@router_v2.get("/players", response_model=list[game.PlayerResponseSchema])
def get_players(db_session: Session = Depends(database_session)) -> \
        list[game.PlayerResponseSchema]:
    """
    Get all players.
    
    Args:
        db_session (Session): The database session.

    Returns:
        list[game.PlayerResponseSchema]: The list of players.

    Raises:
        HTTPException: If an error occurs.
    """
    logger.debug(f"routes_v2.get_players: Entering")
    try:
        players = game.get_players(db_session)
    except Exception as e:
        logger.error(f"routes_v2.get_players: Error getting players: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    logger.info(f"routes_v2.get_players: Players retrieved: {len(players)}")
    
    return TypeAdapter(list[game.PlayerResponseSchema]).validate_python(players)

@router_v2.get("/players/{player_id}",
               response_model=game.PlayerResponseSchema)
def get_player_by_id(player_id: int, 
                       db_session: Session = Depends(database_session)) -> \
        game.PlayerResponseSchema:
    """
    Get a player by ID.
    
    Args:
        player_id (int): The player ID.
        db_session (Session): The database session.

    Returns:
        game.PlayerResponseSchema: The player.

    Raises:
        HTTPException: If the player does not exist or an error occurs.
    """
    logger.debug(f"routes_v2.get_player_by_id: Entering {player_id=}")
    try:
        player = game.get_player_by_id(player_id, db_session)
    except game.PlayerNotFoundError as e:
        logger.error(f"routes_v2.get_player_by_id: Error getting player: {e}")
        raise HTTPException(status_code=404, detail="Player not found")
    except Exception as e:
        logger.error(f"routes_v2.get_player_by_id: Error getting player: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    logger.info(f"routes_v2.get_player_by_id: Player retrieved: {player.name}")
    
    return TypeAdapter(game.PlayerResponseSchema).validate_python(player)

@router_v2.get("/players/name/{player_name}",
               response_model=game.PlayerResponseSchema)
def get_player_by_name(player_name: str, 
                       db_session: Session = Depends(database_session)) -> \
        game.PlayerResponseSchema:
    """
    Get a player by name.
    
    Args:
        player_name (str): The player name.
        db_session (Session): The database session.

    Returns:
        game.PlayerResponseSchema: The player.

    Raises:
        HTTPException: If the player does not exist or an error occurs.
    """
    logger.debug(f"routes_v2.get_player_by_name: Entering {player_name=}")
    try:
        player = game.get_player_by_name(player_name, db_session)
    except game.PlayerNotFoundError as e:
        logger.error(f"routes_v2.get_player_by_name: Error getting player: {e}")
        raise HTTPException(status_code=404, detail="Player not found")
    except Exception as e:
        logger.error(f"routes_v2.get_player_by_name: Error getting player: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    logger.info(f"routes_v2.get_player_by_name: "
                f"Player retrieved: {player.name}")
    
    return TypeAdapter(game.PlayerResponseSchema).validate_python(player)
