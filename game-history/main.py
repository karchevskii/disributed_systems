import uvicorn
from app.consumer import start_redis_consumer

if __name__ == "__main__":
    consumer_thread = start_redis_consumer()
    uvicorn.run("app.main:app", host="0.0.0.0", log_level="debug", port=8002)