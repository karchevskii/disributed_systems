import datetime
from typing import List
from uuid import UUID, uuid4

from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy import JSON

class Base(DeclarativeBase):
    ...

class GameHistory(Base):
    """
    Game history model for the Tic Tac Toe game."
    """
    __tablename__ = "game_history"

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, nullable=False)
    player_x_id: Mapped[str]
    player_o_id: Mapped[str]
    winner: Mapped[str] # id or draw
    game_type: Mapped[str]
    board: Mapped[List[str]] = mapped_column(JSON)
    moves: Mapped[List[dict]] = mapped_column(JSON)
    game_id: Mapped[UUID]
    game_status: Mapped[str]
    created_at: Mapped[datetime.datetime]
    created_by: Mapped[str]

