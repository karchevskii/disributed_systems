import datetime
from uuid import UUID
from pydantic import BaseModel


class GameDTO(BaseModel):
    id: UUID | str
    player_x_id: UUID | str
    player_o_id: UUID | str
    winner: str  # id or draw
    game_type: str
    game_status: str
    board: list[str]
    moves: list[dict]
    game_id: UUID | str
    created_at: datetime.datetime
    created_by: str

    class Config:
        from_attributes = True

class GamesDTO(BaseModel):
    games: list[GameDTO]