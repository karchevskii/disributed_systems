from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logger import get_logger
from app.db import sessionmanager
from contextlib import asynccontextmanager
from app.deps import DBSessionDep
from app.crud import get_games

from app.schemes import GameDTO, GamesDTO

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Function that handles startup and shutdown events.
    """
    yield
    if sessionmanager._engine is not None:
        # Close the DB connection
        await sessionmanager.close()



app = FastAPI(lifespan=lifespan)

logger = get_logger(__name__)


class AuthenticationMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        
        from starlette.requests import Request
        from starlette.responses import JSONResponse
        import httpx
        
        request = Request(scope, receive)

        if request.url.path == "/health":
            return await self.app(scope, receive, send)
        
        # Extract the cookie
        auth_cookie = request.cookies.get("tictactoe")
        
        if not auth_cookie:
            response = JSONResponse(
                status_code=401,
                content={"detail": "Authentication required"}
            )
            return await response(scope, receive, send)
        
        # Validate with users microservice
        async with httpx.AsyncClient() as client:
            try:
                users_response = await client.get(
                    f"{settings.USERS_SERVICE_URL}/users/me",
                    headers={"Cookie": f"tictactoe={auth_cookie}"}
                )
                
                if users_response.status_code != 200:
                    response = JSONResponse(
                        status_code=401,
                        content={"detail": "Invalid authentication token"}
                    )
                    return await response(scope, receive, send)
                
                # Add user info to request state
                request.state.user = users_response.json()
                
            except httpx.RequestError:
                response = JSONResponse(
                    status_code=503,
                    content={"detail": "Authentication service unavailable"}
                )
                return await response(scope, receive, send)
        
        return await self.app(scope, receive, send)

app.add_middleware(AuthenticationMiddleware)

async def get_current_user(request: Request):
    return request.state.user



@app.get("/games", response_model=GamesDTO)
async def get_games_history(
    db: DBSessionDep,
    offset: int = 0,
    limit: int = 10,
    user = Depends(get_current_user)):
    """
    Get all games for the current user.
    """
    games = await get_games(db, user["id"], offset, limit)
    if not games:
        raise HTTPException(status_code=404, detail="No games found")
    
    # Convert SQLAlchemy models to Pydantic models
    game_dtos = [GameDTO.model_validate(game) for game in games]
    
    # Return wrapped in GamesDTO
    return GamesDTO(games=game_dtos)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_URL,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)