import asyncio
import json
import logging
import os

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import redis.asyncio as aioredis

from app.websockets import manager

router = APIRouter()
logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
LIVE_LOG_CHANNEL = "live_log_analysis"

async def redis_listener():
    """Listens to Redis Pub/Sub and broadcasts messages to WebSockets."""
    redis = None
    try:
        redis = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        pubsub = redis.pubsub()
        await pubsub.subscribe(LIVE_LOG_CHANNEL)
        logger.info(f"Subscribed to Redis channel: {LIVE_LOG_CHANNEL}")

        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=None)
            if message and message.get("type") == "message":
                await manager.broadcast(message["data"])
    except asyncio.CancelledError:
        logger.info("Redis listener task cancelled.")
    except Exception as e:
        logger.error(f"Redis listener error: {e}")
    finally:
        if redis:
            await redis.close()
            logger.info("Redis connection closed.")


@router.on_event("startup")
async def startup_event():
    # Start the Redis listener as a background task
    asyncio.create_task(redis_listener())


@router.websocket("/ws/live_logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
