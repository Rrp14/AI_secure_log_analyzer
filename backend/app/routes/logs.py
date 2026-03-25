import threading
from fastapi import APIRouter, Query
from typing import Optional

from app.models.db import log_collection
from app.models.schemas import LogResponse
from app.kafka.producer import start_producer # Import the producer function
from app.services.log_generator import attack_sequence, generate_log

router = APIRouter()

# --- Producer Control Logic ---
producer_thread = None
stop_producer_event = threading.Event()

@router.post("/producer/start", tags=["Producer Control"])
async def start_log_producer():
    """
    Starts the Kafka log producer in a background thread to simulate live traffic.
    This is ideal for demonstrating the real-time analysis on the frontend.
    """
    global producer_thread, stop_producer_event
    if producer_thread and producer_thread.is_alive():
        return {"status": "Producer is already running."}

    stop_producer_event.clear()
    # The `start_producer` function from your producer.py will be run in a separate thread
    producer_thread = threading.Thread(target=start_producer, args=(stop_producer_event,))
    producer_thread.start()
    
    return {"status": "Kafka log producer started."}


@router.post("/producer/stop", tags=["Producer Control"])
async def stop_log_producer():
    """
    Stops the running Kafka log producer.
    """
    global producer_thread, stop_producer_event
    if not producer_thread or not producer_thread.is_alive():
        return {"status": "Producer is not running."}

    stop_producer_event.set()
    producer_thread.join(timeout=5)
    
    if producer_thread.is_alive():
        return {"status": "Producer did not stop in time."}
    
    return {"status": "Kafka log producer stopped."}


@router.get("/producer/status", tags=["Producer Control"])
async def get_producer_status():
    """
    Checks if the Kafka log producer is currently running.
    """
    if producer_thread and producer_thread.is_alive():
        return {"status": "running"}
    return {"status": "stopped"}
# --- End Producer Control Logic ---


@router.get("/logs", response_model=LogResponse, tags=["Logs & Incidents"])
async def get_logs(
    skip: int = 0,
    limit: int = Query(default=20, le=100),
    ip: Optional[str] = None,
) -> dict:
    """
    Retrieve logs from the database with optional filtering and pagination.
    """
    query = {}
    if ip:
        query["ip"] = ip

    logs_cursor = log_collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
    total = await log_collection.count_documents(query)
    
    logs = []
    async for log in logs_cursor:
        log["_id"] = str(log["_id"])
        logs.append(log)
        
    return {"logs": logs, "total": total}


@router.get("/generate-log")
def generate(log_type: str = "mixed"):
    return {"log": generate_log(log_type)}


@router.get("/generate-attack")
def generate_attack():
    return {"logs": attack_sequence()}