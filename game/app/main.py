import asyncio
from contextlib import asynccontextmanager
import datetime
import json
from typing import Dict, Optional
import uuid
from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import redis

from app.utils import check_winner, best_move
from app.schemes import CreateGameDTO, CreateGameScheme
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(cleanup_stale_games())
    yield

app = FastAPI(title=settings.PROJECT_NAME,
              root_path="/game-service", lifespan=lifespan)


redis_client = redis.Redis(
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

        if request.url.path in ["/game-service/docs", "/game-service/openapi.json", "/game-service/health"]:
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

        # Create Redis pub/sub for cross-instance communication
        self.redis_pubsub = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        ).pubsub()

        # Track our own instance ID to avoid broadcasting to ourselves
        self.instance_id = str(uuid.uuid4())

        # Subscribe to the websocket broadcast channel
        self.redis_pubsub.subscribe('websocket_broadcasts')

        # Flags to indicate if tasks are running
        self.polling_task = None
        self.monitoring_task = None

    async def connect(self, websocket: WebSocket, game_id: str, player_id: str):
        """Connect a player's websocket"""
        await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = {}
        self.active_connections[game_id][player_id] = websocket

        # Ensure tasks are started when first connection happens
        if self.polling_task is None or self.polling_task.done():
            self.start_polling()

    def start_polling(self):
        """Start the polling task if it's not already running"""
        try:
            # Only start if there's a running event loop
            loop = asyncio.get_running_loop()
            self.polling_task = loop.create_task(self._poll_for_messages())

            # Also start monitoring if not already running
            if self.monitoring_task is None or self.monitoring_task.done():
                self.monitoring_task = loop.create_task(
                    self.monitor_connections())
        except RuntimeError:
            # No running event loop - this is fine, we'll start when needed
            logger.info(
                "No event loop running, will start tasks when connections are made")

    async def _poll_for_messages(self):
        """Poll for messages from Redis in an async way"""
        logger.info(
            f"Starting Redis pubsub polling for instance {self.instance_id}")
        try:
            while True:
                try:
                    message = self.redis_pubsub.get_message(timeout=0.01)
                    if message and message['type'] == 'message':
                        await self._handle_pubsub_message(message)
                except Exception as e:
                    logger.error(f"Error in polling loop: {e}")

                # Don't hog the event loop
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            logger.info("Polling task cancelled")
            raise
        except Exception as e:
            logger.error(f"Polling task encountered an error: {e}")
            # Re-raise to let the task fail and potentially be restarted
            raise

    def disconnect(self, game_id: str, player_id: str):
        """Disconnect a player"""
        if game_id in self.active_connections:
            if player_id in self.active_connections[game_id]:
                del self.active_connections[game_id][player_id]
            if not self.active_connections[game_id]:  # If empty
                del self.active_connections[game_id]

        # Stop tasks if no more connections
        if not self.active_connections:
            if self.polling_task:
                self.polling_task.cancel()
                self.polling_task = None
            if self.monitoring_task:
                self.monitoring_task.cancel()
                self.monitoring_task = None

    async def _handle_pubsub_message(self, message):
        """Handle incoming pub/sub messages"""
        try:
            data = json.loads(message['data'])

            # Skip messages from our own instance
            if data.get('instance_id') == self.instance_id:
                return

            game_id = data.get('game_id')
            exclude_player = data.get('exclude_player')
            payload = data.get('payload')

            # Forward the message to all local connections for this game
            if game_id in self.active_connections:
                for player_id, conn in self.active_connections[game_id].items():
                    if player_id != exclude_player:
                        try:
                            await conn.send_json(payload)
                        except Exception as e:
                            logger.error(
                                f"Error sending to player {player_id}: {e}")
        except Exception as e:
            logger.error(f"Error processing pub/sub message: {e}")

    async def send_personal_message(self, message: dict, game_id: str, player_id: str):
        """Send message to a specific player"""
        if game_id in self.active_connections and player_id in self.active_connections[game_id]:
            await self.active_connections[game_id][player_id].send_json(message)

    async def broadcast(self, message: dict, game_id: str, exclude: Optional[str] = None):
        """Broadcast a message to all players in a game across all instances"""
        # First, send to all local connections
        if game_id in self.active_connections:
            for player_id, connection in self.active_connections[game_id].items():
                if player_id != exclude:
                    try:
                        await connection.send_json(message)
                    except Exception as e:
                        logger.error(
                            f"Error broadcasting to player {player_id}: {e}")

        # Then, publish to Redis for other instances
        redis_message = {
            'instance_id': self.instance_id,
            'game_id': game_id,
            'exclude_player': exclude,
            'payload': message
        }

        # Use the global redis client for publishing
        try:
            redis_client.publish('websocket_broadcasts',
                                 json.dumps(redis_message))
        except Exception as e:
            logger.error(f"Error publishing broadcast to Redis: {e}")

    async def monitor_connections(self):
        """Monitor active connections and handle timeouts"""
        while True:
            try:
                games_to_check = list(self.active_connections.keys())

                for game_id in games_to_check:
                    # Get game data
                    game_data_str = redis_client.get(f"game:{game_id}")
                    if not game_data_str:
                        continue

                    game_data = json.loads(game_data_str)

                    # Only monitor active multiplayer games
                    if game_data["status"] != "active" or game_data["type"] != "multiplayer":
                        continue

                    # Check if we should have two players but only one is connected
                    players = list(self.active_connections[game_id].keys())
                    if len(players) == 1 and game_data["players"]["x"] and game_data["players"]["o"]:
                        connected_player_id = players[0]

                        # Determine the disconnected player and symbols
                        disconnected_player_id = None
                        connected_symbol = None
                        disconnected_symbol = None

                        if connected_player_id == game_data["players"]["x"]:
                            disconnected_player_id = game_data["players"]["o"]
                            connected_symbol = "x"
                            disconnected_symbol = "o"
                        else:
                            disconnected_player_id = game_data["players"]["x"]
                            connected_symbol = "o"
                            disconnected_symbol = "x"

                        # Check if we've waited long enough (30 seconds) since last activity
                        # to declare a disconnect win
                        last_activity_time = datetime.datetime.now()
                        if game_data["moves"]:
                            last_move_time = datetime.datetime.fromisoformat(
                                game_data["moves"][-1]["timestamp"])
                            last_activity_time = last_move_time

                        time_since_last_activity = (
                            datetime.datetime.now() - last_activity_time).total_seconds()

                        if time_since_last_activity > 30:  # 30 seconds timeout
                            # Mark game as completed with the connected player as winner
                            game_data["status"] = "completed"
                            game_data["winner"] = connected_symbol

                            # Add disconnect information
                            game_data["moves"].append({
                                "player": disconnected_player_id,
                                "symbol": disconnected_symbol,
                                "position": None,
                                "action": "disconnect_timeout",
                                "timestamp": datetime.datetime.now().isoformat()
                            })

                            # Save to Redis
                            redis_client.set(
                                f"game:{game_id}", json.dumps(game_data))
                            redis_client.xadd("completed_games", {
                                              "data": json.dumps(game_data)})

                            # Notify the remaining player
                            try:
                                connected_ws = self.active_connections[game_id][connected_player_id]
                                await connected_ws.send_json({
                                    "type": "game_state",
                                    "game": game_data,
                                    "disconnection": True,
                                    "message": f"Your opponent disconnected. You win!"
                                })
                            except Exception as e:
                                logger.error(
                                    f"Error notifying player about disconnect win: {e}")

                            asyncio.create_task(cleanup_game(game_id))

            except Exception as e:
                logger.error(f"Error in connection monitoring: {e}")

            await asyncio.sleep(5)  # Check every 5 seconds


# Initialize the manager
manager = ConnectionManager()


async def cleanup_game(game_id: str, delay_seconds: int = 10):
    """
    Delete a game from Redis after an optional delay to ensure clients receive final state.

    Args:
        game_id: The ID of the game to delete
        delay_seconds: Number of seconds to wait before deletion (default 10)
    """
    if delay_seconds > 0:
        await asyncio.sleep(delay_seconds)

    # Delete the game data
    redis_client.delete(f"game:{game_id}")
    # Also remove from open games set if present
    redis_client.srem("open_games", game_id)
    logger.info(f"Cleaned up game {game_id} from Redis")


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
                headers={
                    "Cookie": f"tictactoe={websocket.cookies['tictactoe']}"}
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
    game_data_str = redis_client.get(f"game:{game_id}")
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
    logger.debug(
        f"User {user['id']} connected to game {game_id} as {player_symbol}")

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
                    game_data_str = redis_client.get(f"game:{game_id}")
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
                        redis_client.xadd("completed_games", {
                                          "data": json.dumps(game_data)})
                        # Schedule cleanup
                        asyncio.create_task(cleanup_game(game_id))
                    elif "" not in game_data["board"]:  # Board is full
                        game_data["status"] = "completed"
                        game_data["winner"] = "draw"
                        redis_client.xadd("completed_games", {
                                          "data": json.dumps(game_data)})
                        # Schedule cleanup
                        asyncio.create_task(cleanup_game(game_id))
                    else:
                        # Switch turns
                        game_data["current_player"] = (
                            game_data["players"]["o"] if game_data["current_player"] == game_data["players"]["x"]
                            else game_data["players"]["x"]
                        )

                    # Save updated game state to Redis
                    redis_client.set(f"game:{game_id}", json.dumps(game_data))

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
                redis_client.set(f"game:{game_id}", json.dumps(game_data))
                logger.debug(
                    f"Saved initial game state to Redis for game {game_id}")

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
                    game_data_str = redis_client.get(f"game:{game_id}")
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
                        redis_client.xadd("completed_games", {
                                          "data": json.dumps(game_data)})
                        redis_client.set(
                            f"game:{game_id}", json.dumps(game_data))
                        await websocket.send_json({
                            "type": "game_state",
                            "game": game_data
                        })
                        # Schedule cleanup
                        asyncio.create_task(cleanup_game(game_id))
                        continue
                    elif "" not in game_data["board"]:  # Board is full
                        game_data["status"] = "completed"
                        game_data["winner"] = "draw"
                        redis_client.xadd("completed_games", {
                            "data": json.dumps(game_data)})
                        redis_client.set(
                            f"game:{game_id}", json.dumps(game_data))
                        await websocket.send_json({
                            "type": "game_state",
                            "game": game_data
                        })
                        # Schedule cleanup
                        asyncio.create_task(cleanup_game(game_id))
                        continue

                    # Change turn to bot
                    bot_symbol = "x" if player_symbol == "o" else "o"
                    game_data["current_player"] = "bot"

                    # Save interim state before bot makes its move
                    redis_client.set(f"game:{game_id}", json.dumps(game_data))
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
                        redis_client.xadd("completed_games", {
                            "data": json.dumps(game_data)})
                    elif "" not in game_data["board"]:  # Board is full
                        game_data["status"] = "completed"
                        game_data["winner"] = "draw"
                        redis_client.xadd("completed_games", {
                            "data": json.dumps(game_data)})

                    # Change turn back to player
                    game_data["current_player"] = user["id"]

                    # Save updated game state to Redis
                    redis_client.set(f"game:{game_id}", json.dumps(game_data))

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

        # Get fresh game data
        game_data_str = redis_client.get(f"game:{game_id}")
        if game_data_str:
            game_data = json.loads(game_data_str)

            # Only handle active multiplayer games
            if game_data["status"] == "active" and game_data["type"] == "multiplayer":
                # Mark game as completed with the other player as winner
                game_data["status"] = "completed"

                # Determine winner (the player who didn't disconnect)
                other_player_id = None
                if user["id"] == game_data["players"]["x"]:
                    game_data["winner"] = "o"  # Other player wins
                    other_player_id = game_data["players"]["o"]
                else:
                    game_data["winner"] = "x"  # Other player wins
                    other_player_id = game_data["players"]["x"]

                # Add disconnect information to the moves list
                game_data["moves"].append({
                    "player": user["id"],
                    "symbol": player_symbol,
                    "position": None,  # No position for disconnect
                    "action": "disconnect",
                    "timestamp": datetime.datetime.now().isoformat()
                })

                # Save to Redis
                redis_client.set(f"game:{game_id}", json.dumps(game_data))

                # Record the completed game
                redis_client.xadd("completed_games", {
                                  "data": json.dumps(game_data)})

                # Notify the remaining player about the win
                await manager.broadcast(
                    {
                        "type": "game_state",
                        "game": game_data,
                        "disconnection": True,
                        "message": f"Player {player_symbol} disconnected. You win!"
                    },
                    game_id
                )
                # Schedule cleanup
                asyncio.create_task(cleanup_game(game_id))
            elif game_data["status"] == "waiting" and game_data["type"] == "multiplayer" and game_data["created_by"] == user["id"]:
                # Creator of a waiting game disconnected, mark the game as abandoned
                game_data["status"] = "abandoned"

                # Record the abandonment in moves list
                game_data["moves"].append({
                    "player": user["id"],
                    "symbol": player_symbol,
                    "position": None,
                    "action": "creator_abandoned",
                    "timestamp": datetime.datetime.now().isoformat()
                })

                # Update Redis and remove from open games
                redis_client.set(f"game:{game_id}", json.dumps(game_data))
                redis_client.srem("open_games", game_id)

                logger.info(
                    f"Game {game_id} marked as abandoned after creator disconnected")
                # Schedule cleanup
                asyncio.create_task(cleanup_game(game_id))
            else:
                # Just notify about disconnection for non-active or bot games
                await manager.broadcast(
                    {"type": "player_disconnected", "player": player_symbol},
                    game_id
                )


@app.get("/games/open", response_model=list[CreateGameDTO])
async def get_open_games(user=Depends(get_current_user)):
    # Get list of open game IDs
    open_game_ids = redis_client.smembers("open_games")

    open_games = []
    for game_id in open_game_ids:
        game_data_str = redis_client.get(f"game:{game_id}")
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
        current_player = user["id"]  # Player X starts
        if type == "bot":
            players["o"] = "bot"
            status = "active"
    else:
        players = {"x": None, "o": user["id"]}
        current_player = None  # Will be set when player X joins
        if type == "bot":
            players["x"] = "bot"
            current_player = "bot"  # Bot starts as X
            status = "active"
        else:
            current_player = None  # Will be set when player X joins

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
    redis_client.set(f"game:{game_id}", json.dumps(game_data))

    # Add to the list of open games if it's a multiplayer game waiting for opponents
    if type == "multiplayer" and (players["x"] is None or players["o"] is None):
        redis_client.sadd("open_games", game_id)

    return CreateGameDTO(**game_data)


@app.post("/game/join/{game_id}")
async def join_game(game_id: str, user=Depends(get_current_user)):
    # Get game from Redis
    game_data_str = redis_client.get(f"game:{game_id}")
    if not game_data_str:
        raise HTTPException(status_code=404, detail="Game not found")

    game_data = json.loads(game_data_str)

    # Check if game is joinable
    if game_data["status"] != "waiting" or game_data["type"] != "multiplayer":
        raise HTTPException(
            status_code=400, detail="Game is not available to join")

    # Check if user is not already in the game
    if user["id"] == game_data["players"]["x"]:
        raise HTTPException(
            status_code=400, detail="You already joined this game as player x")
    if user["id"] == game_data["players"]["o"]:
        raise HTTPException(
            status_code=400, detail="You already joined this game as player o")

    # Join as another player
    if game_data["players"]["x"] is None:
        game_data["players"]["x"] = user["id"]
    else:  # Must be joining as player "o"
        game_data["players"]["o"] = user["id"]

    # Determine whose turn it should be based on number of moves
    num_moves = len(game_data["moves"])

    if num_moves % 2 == 0:
        game_data["current_player"] = game_data["players"]["x"]
    else:
        game_data["current_player"] = game_data["players"]["o"]

    # Set game to active now that both players are joined
    game_data["status"] = "active"

    # Update game in Redis
    redis_client.set(f"game:{game_id}", json.dumps(game_data))
    redis_client.srem("open_games", game_id)  # Remove from open games

    return game_data


@app.get("/health")
async def health_check():
    return {"status": "ok"}


allowed_origins = [
    settings.CORS_URL,
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


async def cleanup_stale_games():
    """Background task to clean up old games from Redis"""
    try:
        while True:
            try:
                # Get all game keys
                game_keys = redis_client.keys("game:*")
                current_time = datetime.datetime.now()

                for game_key in game_keys:
                    game_data_str = redis_client.get(game_key)
                    if not game_data_str:
                        continue

                    game_data = json.loads(game_data_str)
                    game_id = game_data["id"]

                    # Check if game is already completed or abandoned
                    if game_data["status"] in ["completed", "abandoned"]:
                        # Remove completed games older than 5 minutes
                        if "moves" in game_data and game_data["moves"]:
                            last_move_time = datetime.datetime.fromisoformat(
                                game_data["moves"][-1]["timestamp"])
                            if (current_time - last_move_time).total_seconds() > 300:  # 5 minutes
                                await cleanup_game(game_id, delay_seconds=0)

                    # Check for old waiting games
                    elif game_data["status"] == "waiting":
                        created_time = datetime.datetime.fromisoformat(
                            game_data["created_at"])
                        # Remove waiting games older than 30 minutes
                        if (current_time - created_time).total_seconds() > 1800:  # 30 minutes
                            game_data["status"] = "expired"
                            redis_client.set(game_key, json.dumps(game_data))
                            await cleanup_game(game_id, delay_seconds=0)
                            logger.info(
                                f"Expired stale waiting game {game_id}")
            except Exception as e:
                logger.error(f"Error in cleanup_stale_games: {e}")

            await asyncio.sleep(300)  # Run every 5 minutes
    except asyncio.CancelledError:
        logger.info("Stale game cleanup task cancelled")
