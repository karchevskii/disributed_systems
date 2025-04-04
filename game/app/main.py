import datetime
import json
from typing import Dict, Optional
import uuid
from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import redis

from app.schemes import CreateGameDTO, CreateGameScheme
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

app = FastAPI()


redis = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD,
    decode_responses=True
)

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
        
        if request.url.path in ["/docs", "/openapi.json", "/health"]:
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

class ConnectionManager:
    def __init__(self):
        # {game_id: {player_id: WebSocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, game_id: str, player_id: str):
        await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = {}
        self.active_connections[game_id][player_id] = websocket

    def disconnect(self, game_id: str, player_id: str):
        if game_id in self.active_connections:
            if player_id in self.active_connections[game_id]:
                del self.active_connections[game_id][player_id]
            if not self.active_connections[game_id]:  # If empty
                del self.active_connections[game_id]

    async def send_personal_message(self, message: dict, game_id: str, player_id: str):
        if game_id in self.active_connections and player_id in self.active_connections[game_id]:
            await self.active_connections[game_id][player_id].send_json(message)

    async def broadcast(self, message: dict, game_id: str, exclude: Optional[str] = None):
        if game_id in self.active_connections:
            for player_id, connection in self.active_connections[game_id].items():
                if player_id != exclude:
                    await connection.send_json(message)

manager = ConnectionManager()

def minimax(board, is_maximizing):
    winner = check_winner(board)
    if winner == "x":
        return 1
    if winner == "o":
        return -1
    if "" not in board:
        return 0
    
    if is_maximizing:
        best_score = -float("inf")
        for i in range(9):
            if board[i] == "":
                board[i] = "x"
                score = minimax(board, False)
                board[i] = ""
                best_score = max(score, best_score)
        return best_score
    else:
        best_score = float("inf")
        for i in range(9):
            if board[i] == "":
                board[i] = "o"
                score = minimax(board, True)
                board[i] = ""
                best_score = min(score, best_score)
        return best_score

def best_move(board):
    best_score = -float("inf")
    move = None
    for i in range(9):
        if board[i] == "":
            board[i] = "x"
            score = minimax(board, False)
            board[i] = ""
            if score > best_score:
                best_score = score
                move = i
    return move

@app.websocket("/ws/game/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    # Authenticate user with token from query parameter
    import httpx

    logger.info(f"WebSocket connection request for game {game_id}")
    logger.debug(f"Headers: {websocket.cookies}")
    logger.debug(f"Query params: {websocket.query_params}")

    async with httpx.AsyncClient() as client:
        try:
            users_response = await client.get(
                f"{settings.USERS_SERVICE_URL}/users/me",
                headers={"Cookie": f"tictactoe={websocket.cookies['tictactoe']}"}
            )
            print(users_response)
            
            if users_response.status_code != 200:
                await websocket.close(code=1008, reason="Invalid authentication")
                logger.error("Invalid authentication")
                return
            
            logger.debug("User authenticated successfully")
            user = users_response.json()
            
        except httpx.RequestError:
            await websocket.close(code=1013, reason="Authentication service unavailable")
            logger.error("Authentication service unavailable")
            return
    
    # Get game from Redis
    game_data_str = redis.get(f"game:{game_id}")
    if not game_data_str:
        await websocket.close(code=1008, reason="Game not found")
        return
    
    game_data = json.loads(game_data_str)
    
    # Check if user is a player in this game
    if user["id"] not in [game_data["players"]["x"], game_data["players"]["o"]]:
        await websocket.close(code=1008, reason="You are not a player in this game")
        logger.debug("User is not a player in this game")
        return
    
    # Determine player's symbol (X or O)
    player_symbol = "x" if user["id"] == game_data["players"]["x"] else "o"
    
    # Connect to WebSocket
    await manager.connect(websocket, game_id, user["id"])
    logger.debug(f"User {user['id']} connected to game {game_id} as {player_symbol}")
    
    try:
        # Notify all connected players that a new player has connected
        await manager.broadcast(
            {"type": "player_connected", "player": player_symbol},
            game_id
        )
        
        # Initial game state
        await websocket.send_json({
            "type": "game_state",
            "game": game_data
        })
        logger.debug(f"Sent initial game state to {user['id']}")
        
        # Multiplayer game loop
        if game_data["type"] == "multiplayer":
            logger.debug("Starting multiplayer game loop")
            while True:
                data = await websocket.receive_json()
                
                # Handle different message types
                if data["type"] == "move":
                    # Get fresh game state from Redis
                    game_data_str = redis.get(f"game:{game_id}")
                    if not game_data_str:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Game not found"
                        })
                        continue
                    
                    game_data = json.loads(game_data_str)
                    
                    # Check if it's this player's turn
                    if game_data["current_player"] != user["id"]:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Not your turn"
                        })
                        continue
                    
                    # Check if move is valid
                    position = data["position"]
                    if not (0 <= position < 9) or game_data["board"][position] != "":
                        await websocket.send_json({
                            "type": "error",
                            "message": "Invalid move"
                        })
                        continue
                    
                    # Apply the move
                    game_data["board"][position] = player_symbol

                    # record the move
                    game_data["moves"].append({
                        "player": user["id"],
                        "symbol": player_symbol,
                        "position": position,
                        "timestamp": datetime.datetime.now().isoformat()
                    })
                    
                    # Check for win or draw
                    winner = check_winner(game_data["board"])
                    if winner:
                        game_data["winner"] = winner
                        game_data["status"] = "completed"
                        # send complete game to Redis message queue to be saved in the database by another service
                        redis.xadd("completed_games", {"data": json.dumps(game_data)})
                    elif "" not in game_data["board"]:  # Board is full
                        game_data["status"] = "completed"
                        game_data["winner"] = "draw"
                        redis.xadd("completed_games", {"data": json.dumps(game_data)})
                    else:
                        # Switch turns
                        game_data["current_player"] = (
                            game_data["players"]["o"] if game_data["current_player"] == game_data["players"]["x"] 
                            else game_data["players"]["x"]
                        )
                    
                    # Save updated game state to Redis
                    redis.set(f"game:{game_id}", json.dumps(game_data))
                    
                    # Broadcast updated game state to all players
                    await manager.broadcast(
                        {
                            "type": "game_state",
                            "game": game_data
                        },
                        game_id
                    )

                elif data["type"] == "chat":
                    # Broadcast chat message to all players
                    await manager.broadcast(
                        {
                            "type": "chat",
                            "message": data["message"],
                            "sender": player_symbol
                        },
                        game_id
                    )
        
        # Bot game loop
        if game_data["type"] == "bot":
            logger.debug("Starting bot game loop")
            # If bot starts (bot is X), make first move immediately
            if game_data["current_player"] == "bot" and game_data["players"]["x"] == "bot":
                # Bot plays as X and makes the first move
                bot_symbol = "x"
                
                # Simple strategy for first move - choose center or corner
                bot_position = 4  # Center position
                
                # Apply bot's move
                game_data["board"][bot_position] = bot_symbol
                
                # Record the bot's move
                game_data["moves"].append({
                    "player": "bot",
                    "symbol": bot_symbol,
                    "position": bot_position,
                    "timestamp": datetime.datetime.now().isoformat()
                })
                
                # Change turn to player
                game_data["current_player"] = user["id"]
                
                # Save updated game state to Redis
                redis.set(f"game:{game_id}", json.dumps(game_data))
                logger.debug(f"Saved initial game state to Redis for game {game_id}")
                
                # Send updated game state to player
                await websocket.send_json({
                    "type": "game_state",
                    "game": game_data
                })
            
            # Then enter the game loop to handle player moves and subsequent bot moves
            while True:
                data = await websocket.receive_json()
                
                # Handle different message types
                if data["type"] == "move":
                    # Get fresh game state from Redis
                    game_data_str = redis.get(f"game:{game_id}")
                    if not game_data_str:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Game not found"
                        })
                        continue
                    
                    game_data = json.loads(game_data_str)
                    
                    # Check if game is already completed
                    if game_data["status"] == "completed":
                        await websocket.send_json({
                            "type": "error",
                            "message": "Game already completed"
                        })
                        continue
                    
                    # Check if it's player's turn
                    if game_data["current_player"] != user["id"]:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Not your turn"
                        })
                        continue
                    
                    # Check if move is valid
                    position = data["position"]
                    if not (0 <= position < 9) or game_data["board"][position] != "":
                        await websocket.send_json({
                            "type": "error",
                            "message": "Invalid move"
                        })
                        continue
                    
                    # Apply the player's move
                    game_data["board"][position] = player_symbol
                    
                    # Record the move
                    game_data["moves"].append({
                        "player": user["id"],
                        "symbol": player_symbol,
                        "position": position,
                        "timestamp": datetime.datetime.now().isoformat()
                    })
                    
                    # Check for win or draw after player's move
                    winner = check_winner(game_data["board"])
                    if winner:
                        game_data["winner"] = winner
                        game_data["status"] = "completed"
                        redis.xadd("completed_games", {"data": json.dumps(game_data)})
                        redis.set(f"game:{game_id}", json.dumps(game_data))
                        await websocket.send_json({
                            "type": "game_state",
                            "game": game_data
                        })
                        continue
                    elif "" not in game_data["board"]:  # Board is full
                        game_data["status"] = "completed"
                        game_data["winner"] = "draw"
                        redis.xadd("completed_games", {"data": json.dumps(game_data)})
                        redis.set(f"game:{game_id}", json.dumps(game_data))
                        await websocket.send_json({
                            "type": "game_state",
                            "game": game_data
                        })
                        continue
                    
                    # Change turn to bot
                    bot_symbol = "x" if player_symbol == "o" else "o"
                    game_data["current_player"] = "bot"
                    
                    # Save interim state before bot makes its move
                    redis.set(f"game:{game_id}", json.dumps(game_data))
                    await websocket.send_json({
                        "type": "game_state",
                        "game": game_data
                    })
                    
                    # Bot's turn
                    bot_position = None
                    if bot_symbol == "x":
                        # X plays to win using minimax
                        bot_position = best_move(game_data["board"])
                    else:
                        # O plays defensively
                        # Try to block a winning move first
                        for i in range(9):
                            if game_data["board"][i] == "":
                                # Test if player would win with this move
                                game_data["board"][i] = player_symbol
                                if check_winner(game_data["board"]) == player_symbol:
                                    bot_position = i  # Block this winning move
                                    game_data["board"][i] = ""
                                    break
                                game_data["board"][i] = ""
                        
                        # If no blocking needed, prefer center
                        if bot_position is None and game_data["board"][4] == "":
                            bot_position = 4
                        
                        # Then corners
                        if bot_position is None:
                            corners = [0, 2, 6, 8]
                            for corner in corners:
                                if game_data["board"][corner] == "":
                                    bot_position = corner
                                    break
                        
                        # Then any available spot
                        if bot_position is None:
                            for i in range(9):
                                if game_data["board"][i] == "":
                                    bot_position = i
                                    break
                    
                    # Apply bot's move
                    game_data["board"][bot_position] = bot_symbol
                    
                    # Record the bot's move
                    game_data["moves"].append({
                        "player": "bot",
                        "symbol": bot_symbol,
                        "position": bot_position,
                        "timestamp": datetime.datetime.now().isoformat()
                    })
                    
                    # Check for win or draw after bot's move
                    winner = check_winner(game_data["board"])
                    if winner:
                        game_data["winner"] = winner
                        game_data["status"] = "completed"
                        redis.xadd("completed_games", {"data": json.dumps(game_data)})
                    elif "" not in game_data["board"]:  # Board is full
                        game_data["status"] = "completed"
                        game_data["winner"] = "draw"
                        redis.xadd("completed_games", {"data": json.dumps(game_data)})
                    
                    # Change turn back to player
                    game_data["current_player"] = user["id"]
                    
                    # Save updated game state to Redis
                    redis.set(f"game:{game_id}", json.dumps(game_data))
                    
                    # Send updated game state to player
                    await websocket.send_json({
                        "type": "game_state",
                        "game": game_data
                    })
                
                elif data["type"] == "chat":
                    # Just echo the chat message back for bot games
                    await websocket.send_json({
                        "type": "chat",
                        "message": data["message"],
                        "sender": player_symbol
                    })
                    
                    # Add a bot response
                    bot_responses = [
                        "Interesting move...",
                        "I'm calculating my next move.",
                        "Let me think about this.",
                        "Are you sure about that?",
                        "Hmm, I see what you're doing.",
                        "Nice try!",
                        "I'm enjoying our game."
                    ]
                    import random
                    bot_message = random.choice(bot_responses)
                    
                    await websocket.send_json({
                        "type": "chat",
                        "message": bot_message,
                        "sender": "bot"
                    })

    except WebSocketDisconnect:
        # Handle disconnection
        manager.disconnect(game_id, user["id"])
        await manager.broadcast(
            {"type": "player_disconnected", "player": player_symbol},
            game_id
        )

# Helper function to check for a winner
def check_winner(board):
    # Check rows
    for i in range(0, 9, 3):
        if board[i] == board[i+1] == board[i+2] != "":
            return board[i]
    
    # Check columns
    for i in range(3):
        if board[i] == board[i+3] == board[i+6] != "":
            return board[i]
    
    # Check diagonals
    if board[0] == board[4] == board[8] != "":
        return board[0]
    if board[2] == board[4] == board[6] != "":
        return board[2]
    
    return None


@app.get("/games/open", response_model=list[CreateGameDTO])
async def get_open_games(user=Depends(get_current_user)):
    # Get list of open game IDs
    open_game_ids = redis.smembers("open_games")
    
    open_games = []
    for game_id in open_game_ids:
        game_data_str = redis.get(f"game:{game_id}")
        if game_data_str:
            game_data = json.loads(game_data_str)
            # Only show games that the user is not already in and that are waiting for players
            if game_data["players"]["x"] != user["id"] and game_data["players"]["o"] != user["id"]: 
                open_games.append(game_data)
    
    return open_games


@app.post("/game/create", response_model=CreateGameDTO)
async def create_game(data: CreateGameScheme, user=Depends(get_current_user)):
    # Generate a unique game ID
    game_id = str(uuid.uuid4())
    
    type = data.type.value
    status = "waiting"

    # Create game data structure
    # X always starts
    if data.symbol.value == "x":
        players = {"x": user["id"], "o": None}
        current_player = user["id"]
        if type == "bot":
            players["o"] = "bot"
            status = "active"
    else:
        players = {"x": None, "o": user["id"]}
        if type == "bot":
            players["x"] = "bot"        
            current_player = "bot"
            status = "active"
        else:
            current_player = None

    game_data = {
        "id": game_id,
        "type": type,
        "status": status,
        "board": [""] * 9,  # Empty 3x3 board
        "current_player": current_player,
        "players": players,
        "winner": None,
        "created_at": datetime.datetime.now().isoformat(),
        "created_by": user["id"],
        "moves": []
    }
    
    # Store game in Redis
    redis.set(f"game:{game_id}", json.dumps(game_data))
    
    # Add to user's games list and to the list of open games
    # redis.sadd(f"user:{user['id']}:games", game_id)
    if type == "multiplayer":
        redis.sadd("open_games", game_id)
    
    return CreateGameDTO(**game_data)

@app.post("/game/join/{game_id}")
async def join_game(game_id: str, user=Depends(get_current_user)):
    # Get game from Redis
    game_data_str = redis.get(f"game:{game_id}")
    if not game_data_str:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game_data = json.loads(game_data_str)
    
    # Check if game is joinable
    if game_data["status"] != "waiting" or game_data["type"] != "multiplayer":
        raise HTTPException(status_code=400, detail="Game is not available to join")
    
    # Check if user is not already in the game
    if user["id"] == game_data["players"]["x"]:
        raise HTTPException(status_code=400, detail="You already joined this game as player x")
    if user["id"] == game_data["players"]["o"]:
        raise HTTPException(status_code=400, detail="You already joined this game as player o")
    
    # Join as another player
    if game_data["players"]["x"] is None:
        game_data["players"]["x"] = user["id"]
        game_data["current_player"] = user["id"]
    elif game_data["players"]["o"] is None:
        game_data["players"]["o"] = user["id"]
        
    game_data["status"] = "active"
    # Update game in Redis
    redis.set(f"game:{game_id}", json.dumps(game_data))
    redis.srem("open_games", game_id)  # Remove from open games
    # redis.sadd(f"user:{user['id']}:games", game_id)  # Add to user's games
    
    return game_data

@app.get("/health")
async def health_check():
    return {"status": "ok"}


allowed_origins = [
    settings.FRONTEND_URL,
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)