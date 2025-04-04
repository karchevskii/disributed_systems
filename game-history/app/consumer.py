import threading
import asyncio
import redis
import json
import os
import socket
from app.core.config import settings
from app.core.logger import get_logger
from app.crud import create_game_history
from app.db import DatabaseSessionManager


logger = get_logger(__name__)

def get_redis_client():
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
        decode_responses=True
    )

_consumer_sessionmanager = None
_consumer_thread = None

def is_first_worker():
    """Determine if this is the first worker by checking Redis"""
    client = get_redis_client()
    
    # Use a Redis key as a lock
    hostname = socket.gethostname()
    pid = os.getpid()
    lock_key = "game_history_consumer_lock"
    
    # Try to set the key with our hostname:pid if it doesn't exist yet
    # NX = only set if it doesn't exist, EX = expiry in seconds
    lock_acquired = client.set(lock_key, f"{hostname}:{pid}", nx=True, ex=30)
    
    if lock_acquired:
        logger.info(f"Lock acquired by {hostname}:{pid}, starting consumer")
        
        # Set up a recurring task to refresh the lock
        def refresh_lock():
            try:
                current_value = client.get(lock_key)
                if current_value and current_value.decode() == f"{hostname}:{pid}":
                    client.expire(lock_key, 30)  # Extend expiry
                    threading.Timer(10, refresh_lock).start()
            except Exception as e:
                logger.error(f"Error refreshing lock: {e}")
        
        # Start refreshing the lock
        threading.Timer(10, refresh_lock).start()
        return True
    else:
        logger.info(f"Lock already acquired, skipping consumer start in {hostname}:{pid}")
        current_holder = client.get(lock_key)
        logger.info(f"Current lock holder: {current_holder}")
        return False


async def process_redis_messages():
    global _consumer_sessionmanager

    _consumer_sessionmanager = DatabaseSessionManager(str(settings.DATABASE_URI))

    redis_client = get_redis_client()

    try:
        redis_client.xgroup_create("completed_games", "game_history", id="0", mkstream=True)
        logger.info("Consumer Group created")
    except redis.exceptions.ResponseError:
        logger.info("Consumer Group already exists")

    logger.info("Checking existing messages in stream...")
    all_messages = redis_client.xrange("completed_games", "-", "+")
    logger.info(f"All messages in stream: {all_messages}")
    
    try:
        while True:
            # Read messages from the stream
            try:
                messages = redis_client.xread({"completed_games": "0"}, count=1, block=5000)
                logger.debug(f"Messages read: {messages}")
                if messages:
                    for stream, msg_list in messages:
                        for msg_id, msg_data in msg_list:
                            logger.info(f"Raw message data: {msg_data}")
                            
                            # Extract the nested JSON data
                            if "data" in msg_data:
                                # Parse the nested JSON string
                                try:
                                    game_data = json.loads(msg_data["data"])
                                    logger.info(f"Parsed game data: {game_data}")
                                    
                                    async with _consumer_sessionmanager.session() as db_session:
                                        # Now we have a real session, not just a dependency annotation
                                        try:
                                            await create_game_history(db_session=db_session, game_data=game_data)
                                            logger.info(f"Game history created for game ID: {game_data['id']}")
                                            
                                            # Acknowledge the message
                                            redis_client.xack("completed_games", "game_history", msg_id)
                                            logger.info(f"Acknowledged and stored in DB: {msg_id}")
                                            
                                            # Delete message after processing
                                            redis_client.xdel("completed_games", msg_id)
                                            logger.info(f"Deleted: {msg_id}")
                                        except Exception as e:
                                            # The session.close() will be handled by the context manager
                                            logger.error(f"Error in database operation: {e}")
                                            continue
                                except json.JSONDecodeError as e:
                                    logger.error(f"Failed to parse JSON data: {e}")
                            else:
                                logger.error(f"Message doesn't contain 'data' field: {msg_data}")
            
                else:
                    logger.debug("No new messages. Waiting...")
                    await asyncio.sleep(1)
            except Exception as e:
                logger.info(f"Error processing message: {e}")
                await asyncio.sleep(1)  # Wait before retrying
    finally:
        # Clean up if the consumer exits
        if _consumer_sessionmanager:
            await _consumer_sessionmanager.close()

def run_async_process():
    """Run the async process_redis_messages in an event loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(process_redis_messages())
    finally:
        loop.close()

def start_redis_consumer():
    """Start the Redis consumer in a separate thread"""
    thread = threading.Thread(target=run_async_process, daemon=True)
    thread.start()
    return thread

def ensure_consumer_running():
    """Ensure the consumer is running, starting it if needed"""
    global _consumer_thread
    
    # Only start the consumer if we're the first worker to do so
    if is_first_worker():
        if _consumer_thread is None or not _consumer_thread.is_alive():
            _consumer_thread = start_redis_consumer()
            return _consumer_thread
    return None

# Auto-start on import if not running as main script
if __name__ != "__main__":
    ensure_consumer_running()