import logging
from typing import Generator

from fastapi import Path, HTTPException, Depends
from sqlalchemy.orm import Session

from ..campaign import Campaign
from ..core import get_session

logger = logging.getLogger(__name__)

def database_session() -> Generator[Session, None, None]:
    """
    Dependency to get the database session.

    Yields:
        Session: The database session.
    """
    with get_session() as session:
        try:
            yield session
            logger.debug("server.dependencies.database_session: "
                         "Committing session")
            session.commit()
        except Exception as e:
            logger.error(f"server.dependencies.database_session: "
                         f"Exception caught! Rolling back session: {e}")
            session.rollback()
            raise

def get_campaign_and_collection(
        campaign_short_name: str = Path(
            ..., 
            description="The short name of the campaign"
        ),
        collection_name: str | None = None,
        session: Session = Depends(database_session)
    ) -> tuple[Campaign, str]:
    """
    Dependency to get the campaign object and routed collection string.

    Args:
        campaign_short_name (str): The short name of the campaign.
        collection_name (str | None): The name of the collection. If None, 
                                      the default collection name is used.

    Returns:
        tuple[Campaign, str]: The campaign object and collection string.

    Raises:
        HTTPException: If the campaign is not found.
    """
    try:
        campaign = Campaign.from_db_by_short_name(session, campaign_short_name)
    except ValueError as e:
        logger.error(f"Error getting campaign: {e}")
        raise HTTPException(status_code=404, detail="Campaign not found")

    if collection_name is None:
        collection_name = campaign.metadata.get_default_collection_name()

    return campaign, collection_name
