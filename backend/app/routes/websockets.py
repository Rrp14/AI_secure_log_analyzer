import asyncio
import json
import logging
import os

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import redis.asyncio as aioredis

from app.websockets import manager

router = APIRouter()
logger = logging.getLogger(__name__)

REDIS_URLS = ["redis://redis:6379/0", "redis://localhost:6379/0"]
LIVE_LOG_CHANNEL = "live_log_analysis"

async def redis_listener():
    """Listens to Redis Pub/Sub and broadcasts messages to WebSockets."""
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    print(f"DEBUG: Redis listener task started for {redis_url}")
    
    while True:
        redis_obj = None
        try:
            print(f"DEBUG: Connecting to Redis for WebSockets at {redis_url}...")
            redis_obj = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)
            pubsub = redis_obj.pubsub()
            await pubsub.subscribe(LIVE_LOG_CHANNEL)
            print(f"DEBUG: Subscribed to Redis channel: {LIVE_LOG_CHANNEL}")

            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message.get("type") == "message":
                    data = message["data"]
                    print(f">>> WS BROADCAST: {data[:50]}...")
                    await manager.broadcast(data)
        except Exception as e:
            print(f"DEBUG: Redis listener error for {redis_url}: {e}. Retrying in 5s...")
            if redis_obj:
                await redis_obj.close()
            await asyncio.sleep(5)
        finally:
            if redis_obj:
                try:
                    await redis_obj.close()
                except:
                    pass


@router.get("/ws/status")
async def ws_status():
    return {"active_connections": len(manager.active_connections)}


@router.websocket("/ws/live_logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
