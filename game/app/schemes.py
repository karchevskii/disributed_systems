import datetime
from enum import Enum
from pydantic import BaseModel

class GameType(Enum):
    bot = "bot"
    multiplayer = "multiplayer"

class Symbol(Enum):
    x = "x" # alsways plays first
    o = "o"

class Status(Enum):
    waiting = "waiting"
    active = "active"
    completed = "completed"


class CreateGameDTO(BaseModel):
    id: str
    type: GameType
    status: Status
    board: list[str]
    current_player: str | None
    players: dict[str | None, str | None]
    winner: str | None
    created_at: datetime.datetime
    created_by: str
    moves: list


class CreateGameScheme(BaseModel):
    type: GameType
    symbol: Symbol
