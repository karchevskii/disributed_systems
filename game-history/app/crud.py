from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import GameHistory
from app.core.logger import get_logger

logger = get_logger(__name__)

async def get_games(db_session: AsyncSession, user_id: str, offset: int, limit: int) -> list[GameHistory]:
    """
    Get all games for the current user.
    """
    games = await db_session.execute(
        select(GameHistory).filter(
            (GameHistory.player_x_id == user_id) | (GameHistory.player_o_id == user_id)
        ).offset(offset).limit(limit)
    )
    return games.scalars().all()


async def get_game_by_id(db_session: AsyncSession, game_id: str) -> GameHistory:
    """
    Get a game by its ID.
    """
    game = await db_session.execute(
        select(GameHistory).filter(GameHistory.game_id == game_id)
    )
    return game.scalars().first()

async def create_game_history(db_session: AsyncSession, game_data: dict) -> GameHistory:
    """
    Create a new game history entry.
    """
    try:
        game_history = GameHistory(
            game_id=game_data["id"],
            player_x_id=game_data["players"]["x"],
            player_o_id=game_data["players"]["o"],
            winner=game_data["winner"],
            game_type=game_data["type"],
            game_status=game_data["status"],
            board=game_data["board"],
            moves=game_data["moves"],
            created_at=datetime.fromisoformat(game_data["created_at"]),
            created_by=game_data["created_by"]
        )
        logger.info(f"Creating game history in db: {game_history}")
        db_session.add(game_history)
        await db_session.commit()
        await db_session.refresh(game_history)
        return game_history
    except Exception as e:
        logger.error(f"Error creating game history: {e}")
        await db_session.rollback()
        raise e