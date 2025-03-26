import time
import redis
import os


REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_DB = int(os.environ.get("REDIS_DB", 0))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "password")

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True
)

try:
    redis_client.xgroup_create("completed_games", "game_history", id="0", mkstream=True)
    print("Consumer Group created")
except redis.exceptions.ResponseError:
    print("Consumer Group already exists")

consumer_name = "consumer1"

while True:
    # Read messages from the stream
    messages = redis_client.xreadgroup("game_history", consumer_name, {"completed_games": ">"}, count=1, block=5000)

    if messages:
        for stream, msg_list in messages:
            for msg_id, msg_data in msg_list:
                print(f"Processing: {msg_data}")

                # Simulate processing (store in DB, file, etc.)
                time.sleep(1)

                # Acknowledge the message
                redis_client.xack("completed_games", "game_history", msg_id)
                print(f"Acknowledged: {msg_id}")

                # Delete message after processing
                redis_client.xdel("completed_games", msg_id)
                print(f"Deleted: {msg_id}")
    else:
        print("No new messages. Waiting...")