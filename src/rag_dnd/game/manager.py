from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .enums import PlayerType
from .exceptions import PlayerExistsError, PlayerNotFoundError
from .models import Player, HumanPlayer, AIPlayer
from .schemas import PlayerCreateSchema


# ===========================================================================
# Player management functions
# ===========================================================================
# Player registration functions
# ---------------------------------------------------------------------------
def register_player(player_data: PlayerCreateSchema, session: Session) -> Player:
    """
    Register a new player.

    Args:
        player_data (PlayerCreateSchema): The player data.
        session (Session): The database session.

    Returns:
        Player: The registered player.

    Raises:
        PlayerExistsError: If the player already exists.
        ValueError: If the player type is invalid.

    Examples:
        # Create a human player, using HumanPlayerCreate schema
        >>> player = register_player(HumanPlayerCreate(name="John Doe",
        ... player_type=PlayerType.HUMAN, email="[EMAIL_ADDRESS]"), session)

        # Create an AI player, using AIPlayerCreate schema
        >>> player = register_player(AIPlayerCreate(name="AI Player",
        ...     player_type=PlayerType.AI, ai_provider="openai",
        ...     ai_model="gpt-4"), session)

        # Create a player using PlayerCreateSchema (discriminator)
        >>> player = register_player(PlayerCreateSchema(
        ...     name="John Doe", player_type=PlayerType.HUMAN,
        ...     email="[EMAIL_ADDRESS]" ), session)
    """
    try:
        match player_data.player_type:
            case PlayerType.HUMAN:
                player = HumanPlayer(**player_data.model_dump())
            case PlayerType.AI:
                player = AIPlayer(**player_data.model_dump())
            case _:
                raise ValueError(
                    f"Invalid player type: {player_data.player_type}")
        
        session.add(player)
        session.flush()
        
        return player
    except IntegrityError as e:
        raise PlayerExistsError(
            f"Player {player_data.name} already exists.") from e


# ---------------------------------------------------------------------------
# Player retrieval functions
# ---------------------------------------------------------------------------
def get_players(session: Session) -> list[Player]:
    """
    Get all players.

    Args:
        session (Session): The database session.

    Returns:
        list[Player]: The list of players.
    """
    return session.query(Player).all()

def get_player_by_id(player_id: int, session: Session) -> Player:
    """
    Get a player by ID.

    Args:
        player_id (int): The player ID.
        session (Session): The database session.

    Returns:
        Player: The player.

    Raises:
        PlayerNotFoundError: If the player does not exist.
    """
    player = session.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise PlayerNotFoundError(f"Player #{player_id} not found.")
    return player

def get_player_by_name(player_name: str, session: Session) -> Player:
    """
    Get a player by name.

    Args:
        player_name (str): The player name.
        session (Session): The database session.

    Returns:
        Player: The player.

    Raises:
        PlayerNotFoundError: If the player does not exist.
    """
    player = session.query(Player).filter(Player.name == player_name).first()
    if not player:
        raise PlayerNotFoundError(f"Player '{player_name}' not found.")
    return player
