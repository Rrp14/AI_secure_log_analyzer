import threading
from fastapi import APIRouter, Query
from typing import Optional

from app.models.db import log_collection
from app.models.schemas import LogResponse
from app.kafka.producer import start_producer # Import the producer function
from app.services.log_generator import attack_sequence, generate_log

router = APIRouter()

import os
import redis

# --- REDIS CLIENT ---
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
except:
    redis_client = None

# --- Producer Control Logic ---
# Since producer is a separate container, we use Redis for status

@router.post("/producer/start", tags=["Producer Control"])
async def start_log_producer():
    if redis_client:
        redis_client.set("producer_active", "true")
    return {"status": "Kafka log producer signal sent."}


@router.post("/producer/stop", tags=["Producer Control"])
async def stop_log_producer():
    if redis_client:
        redis_client.set("producer_active", "false")
    return {"status": "Kafka log producer stop signal sent."}


@router.get("/producer/status", tags=["Producer Control"])
async def get_producer_status():
    if redis_client:
        status = redis_client.get("producer_status")
        if status:
            return {"status": status}
    return {"status": "stopped"}
# --- End Producer Control Logic ---


@router.get("/logs", tags=["Logs & Incidents"])
def get_logs(
    skip: int = 0,
    limit: int = Query(default=20, le=100),
    ip: Optional[str] = None,
):
    """
    Retrieve logs from the database with optional filtering and pagination.
    """
    query = {}
    if ip:
        query["ip"] = ip

    logs_cursor = log_collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
    total = log_collection.count_documents(query)

    logs = []
    for log in logs_cursor:
        log["_id"] = str(log["_id"])
        logs.append(log)

    return {"logs": logs, "total": total}


@router.get("/generate-log")
def generate(log_type: str = "mixed"):
    return {"log": generate_log(log_type)}


@router.get("/generate-attack")
def generate_attack():
    return {"logs": attack_sequence()}