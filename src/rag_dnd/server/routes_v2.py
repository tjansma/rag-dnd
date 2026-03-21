"""FastAPI routes for API requests."""
import logging

from fastapi import APIRouter, UploadFile, HTTPException, Depends, Path

from .. import rag
from .upload import temporary_upload
from .schemas import QueryRequest, LLMMessage, ExpandQueryRequest, \
    CreateCampaignRequest, CampaignResponse

logger = logging.getLogger(__name__)

router_v2 = APIRouter(prefix="/v2")

# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

def get_campaign_and_collection(
        campaign_short_name: str = Path(
            ..., 
            description="The short name of the campaign"
        ),
        collection_name: str | None = None
    ) -> tuple[rag.Campaign, str]:
    """
    Dependency to get the campaign object and routed collection string.

    Args:
        campaign_short_name (str): The short name of the campaign.
        collection_name (str | None): The name of the collection. If None, 
                                      the default collection name is used.

    Returns:
        tuple[rag.Campaign, str]: The campaign object and collection string.
    """
    try:
        campaign = rag.Campaign.from_db_by_short_name(campaign_short_name)
    except ValueError as e:
        logger.error(f"Error getting campaign: {e}")
        raise HTTPException(status_code=404, detail="Campaign not found")

    if collection_name is None:
        collection_name = campaign.metadata.get_default_collection_name()

    return campaign, collection_name


# ---------------------------------------------------------------------------
# Campaign routes
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
    campaign = rag.campaign.Campaign.create(
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


@router_v2.get("/campaigns")
def get_campaign_list() -> list[CampaignResponse]:
    """
    Get a list of all campaigns.

    Returns:
        list[CampaignResponse]: The list of campaigns.
    """
    campaigns = rag.campaign.Campaign.list_all()
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

@router_v2.put("/campaigns/{campaign_short_name}/documents", status_code=200)
def update_document(file: UploadFile,
                    campaign_and_collection: tuple[rag.Campaign, str] = Depends(get_campaign_and_collection)
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

    logger.debug(f"Updating document: {file.filename} in collection: {collection_name}")

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
                raise HTTPException(status_code=404, detail="Document does not exist on file system")
    except OSError as e:
        logger.error(f"Error updating document in database: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    logger.info(f"Document updated in database: {file.filename}")


@router_v2.delete("/campaigns/{campaign_short_name}/documents/{filename}")
def delete_document(filename: str,
                    campaign_and_collection: tuple[rag.Campaign, str] = Depends(get_campaign_and_collection)
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

    logger.debug(f"routes_v2.delete_document: Deleting document: {filename} from collection: {collection_name}")
    try:
        campaign.delete_document(filename, collection_name=collection_name)
    except rag.DocumentNotFoundError as e:
        logger.error(f"routes_v2.delete_document: Error deleting document: {e}")
        raise HTTPException(status_code=404, detail="Document not found")
    except Exception as e:
        logger.error(f"routes_v2.delete_document: Error deleting document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    logger.info(f"routes_v2.delete_document: Document deleted from database: {filename}")


@router_v2.post("/campaigns/{campaign_short_name}/query")
def query_campaign(request: QueryRequest,
                   campaign_and_collection: tuple[rag.Campaign, str] = Depends(get_campaign_and_collection)
                   ) -> list[rag.QueryResult]:
    """
    Query the campaign RAG system.
    
    Args:
        request (QueryRequest): The query to ask.
        campaign_short_name (str): The short name of the campaign to query.
    """
    campaign, collection_name = campaign_and_collection

    # Als de body param een specifieke collection_name meestuurt, overschrijft deze
    # de default collection uit de dependency
    if request.collection_name is not None:
        collection_name = request.collection_name

    logger.debug(f"routes_v2.query_campaign: Entering campaign_short_name={campaign.metadata.short_name}, "
                 f"{request=}")
                 
    logger.debug(f"routes_v2.query_campaign: Querying campaign: {campaign.metadata.short_name} "
                 f"in collection: {collection_name}")
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

    logger.info(f"routes_v2.query_campaign: Campaign queried: {campaign.metadata.short_name}")
    return result


# ---------------------------------------------------------------------------
# LLM routes
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
        messages = [ { "role": message.role, "content": message.content } for message in prompt ]
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
