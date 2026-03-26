import os
import time
import json
import random
import threading
import logging
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
import redis

# --- FIX: Import the new advanced_attack_sequence ---
from app.services.log_generator import generate_log, attack_sequence, advanced_attack_sequence

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# --- REDIS STATUS ---
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    logger.info(f"Producer connected to Redis at {REDIS_URL}")
except Exception as e:
    logger.error(f"Producer failed to connect to Redis: {e}")
    redis_client = None

def set_producer_status(status):
    if redis_client:
        try:
            redis_client.set("producer_status", status)
        except:
            pass
# --------------------

TOPIC = os.getenv("KAFKA_TOPIC", "secure_logs") 



producer = None

def create_producer(retries=5, delay=10):
    """
    Attempts to create a KafkaProducer instance with retries.
    This handles the case where Kafka is not yet ready when the app starts.
    """
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
    
    for i in range(retries):
        try:
            logger.info(f"Connecting to Kafka at {bootstrap_servers} (Attempt {i+1}/{retries})...")
            # Explicitly setting api_version can prevent some startup race conditions
            return KafkaProducer(
                bootstrap_servers=bootstrap_servers.split(','),
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                api_version=(0, 10, 2),
                request_timeout_ms=10000 # Increased timeout
            )
        except NoBrokersAvailable:
            if i < retries - 1:
                logger.warning(f"Kafka not ready. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                logger.error("Could not connect to Kafka after multiple retries.")
                raise

def get_producer():
    """
    Gets the singleton KafkaProducer instance, creating it if it doesn't exist.
    """
    global producer
    if producer is None:
        producer = create_producer()
    return producer

# --- END LAZY INITIALIZATION ---


# Attack control
last_attack_time = 0
ATTACK_COOLDOWN = 60  # seconds

# Traffic behavior
NORMAL_SLEEP_RANGE = (1, 3)   # seconds
BURST_MODE_PROB = 0.2         # 20% chance of burst
BURST_COUNT_RANGE = (3, 6)    # logs in burst


def send_log(log):
    try:
        kafka_producer = get_producer()
        if kafka_producer:
            kafka_producer.send(TOPIC, {"log": log, "source": "producer"})
            print("Sent:", log)
    except Exception as e:
        logger.error(f"Failed to get producer or send log: {e}")


def start_producer(stop_event: threading.Event):
    """
    Starts the log producer loop.
    The loop will run until the stop_event is set.
    """
    global last_attack_time
    last_attack_time = 0

    print("Kafka Producer started...")
    set_producer_status("running")

    while not stop_event.is_set():
        try:
            # Check if we should be active
            if redis_client:
                is_active = redis_client.get("producer_active")
                if is_active == "false":
                    set_producer_status("paused")
                    time.sleep(2)
                    continue
                else:
                    set_producer_status("running")
            
            current_time = time.time()
            r = random.random()
            
            # --- RESTRUCTURED PRODUCER LOGIC ---

            # 1. Decide what to do in this iteration
            is_attack_time = (current_time - last_attack_time > ATTACK_COOLDOWN) and (r < 0.15)
            is_burst_time = random.random() < BURST_MODE_PROB

            if is_attack_time:
                # --- ATTACK BLOCK ---
                if random.random() < 0.5:
                    print("\nBRUTE FORCE ATTACK SEQUENCE TRIGGERED\n")
                    logs_to_send = attack_sequence()
                else:
                    print("\nDATA LEAK ATTACK SEQUENCE TRIGGERED\n")
                    logs_to_send = advanced_attack_sequence()

                for log in logs_to_send:
                    send_log(log)
                    # Use a very short sleep *during* the attack
                    time.sleep(random.uniform(0.2, 0.5))
                
                last_attack_time = time.time()
                print("\nATTACK SEQUENCE FINISHED.\n")
                # The main sleep at the end of the loop will provide the pause

            elif is_burst_time:
                # --- BURST BLOCK ---
                burst_count = random.randint(*BURST_COUNT_RANGE)
                for _ in range(burst_count):
                    log = generate_log()
                    send_log(log)
                # No extra sleep needed here

            else:
                # --- NORMAL LOG BLOCK ---
                log = generate_log()
                send_log(log)

            # 2. Apply a consistent pause at the end of EVERY iteration
            # This is the key fix: it prevents an immediate new loop after an attack.
            time.sleep(random.uniform(*NORMAL_SLEEP_RANGE))
            
            # --- END RESTRUCTURED LOGIC ---

        except Exception as e:
            print("Producer error:", e)
            # Add a sleep here too to prevent fast error loops
            time.sleep(5)
    
    print("Kafka Producer stopped.")
    set_producer_status("stopped")


if __name__ == "__main__":
    # This part is now just for manual testing
    stop = threading.Event()
    try:
        start_producer(stop)
    except KeyboardInterrupt:
        stop.set()