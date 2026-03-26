import os
import json
import time
import re
import uuid
import logging
from collections import deque, defaultdict
from datetime import datetime, timezone

import numpy as np
import redis
from kafka import KafkaConsumer
from sklearn.ensemble import IsolationForest
from dotenv import load_dotenv

from app.models.db import incident_collection, log_collection
from app.services.detection import detect_sensitive_data
from app.services.risk import calculate_risk
from app.services.policy import apply_policy

# INIT
load_dotenv()

def get_redis_client():
    hosts = ["redis", "localhost"]
    for h in hosts:
        try:
            client = redis.Redis(host=h, port=6379, db=0, decode_responses=True)
            client.ping()
            print(f"Redis connection successful on host: {h}")
            return client
        except:
            continue
    print("Could not connect to Redis on 'redis' or 'localhost'. Live logs will not be sent.")
    return None

redis_client = get_redis_client()
LIVE_LOG_CHANNEL = "live_log_analysis"
TOPIC = "logs_topic"

logger = logging.getLogger(__name__)
# Use a more detailed logging format
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "secure_logs")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")

# CONFIG
TIME_WINDOW_SECONDS = 10
THRESHOLD = 3
RESET_WINDOW = 15
AI_COOLDOWN = 60
PATTERN_THRESHOLD = 5

# ML MODEL
model = IsolationForest(contamination=0.1, random_state=42)

training_samples = []
MODEL_TRAINED = False

# STATE
ip_state = defaultdict(lambda: {
    "failed_window": deque(),
    "attack_buffer": [],
    "pattern_store": [],
    "attack_active": False,
    "last_detected": 0,
    "last_ai_trigger": 0,
    "request_count": 0,
    "success_count": 0,
    "error_count": 0,
    "last_request_time": None
})

user_ip_map = {}

# HELPERS
def extract_timestamp(log):
    try:
        match = re.match(r"\[(.*?)\]", log)
        if match:
            return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
        return datetime.now()
    except:
        return datetime.now()


def extract_ip(log):
    match = re.search(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", log)
    return match.group(0) if match else None


def extract_user(log):
    match = re.search(r"user '?(\w+)'?", log.lower())
    return match.group(1) if match else None


def build_features(state, is_failed, is_success, is_danger, now):
    if state["last_request_time"]:
        time_gap = (now - state["last_request_time"]).total_seconds()
    else:
        time_gap = 0

    return np.array([[
        state["request_count"],
        state["success_count"],
        state["error_count"],
        len(state["failed_window"]),
        int(is_failed),
        int(is_success),
        int(is_danger),
        time_gap
    ]])


# MAIN CONSUMER
def start_consumer():
    global MODEL_TRAINED

    logger.info("Kafka Consumer started...")

    consumer = None
    while consumer is None:
        try:
            logger.info(f"Attempting to connect to Kafka at {KAFKA_BOOTSTRAP_SERVERS}...")
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                auto_offset_reset='earliest',
                group_id='log-analyzer-group',
            )
            logger.info("KafkaConsumer connected successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka, retrying in 5 seconds... Error: {e}")
            time.sleep(5)

    logger.info(f"Consumer started, listening to topic: {KAFKA_TOPIC}")
    
    # --- FIX: ADD A TOP-LEVEL TRY/EXCEPT BLOCK TO CATCH THE CRASH ---
    try:
        for message in consumer:
            try:
                log_data = json.loads(message.value.decode('utf-8'))

                if log_data.get("source") == "ai":
                    continue

                log = log_data["log"]
                logger.info(f"\nReceived log: {log}")

                now_real = time.time()
                now = extract_timestamp(log)

                # EXTRACT
                ip = extract_ip(log)
                user = extract_user(log)

                is_failed = "failed login" in log.lower()
                is_success = "logged in" in log.lower()
                is_danger = "rm -rf" in log.lower()

                if (ip is None or ip == "unknown") and user:
                    ip = user_ip_map.get(user, "unknown")

                if ip is None:
                    ip = "unknown"

                if is_success and user:
                    user_ip_map[user] = ip

                state = ip_state[ip]

                # COUNTERS
                state["request_count"] += 1
                if is_success:
                    state["success_count"] += 1
                if is_failed:
                    state["error_count"] += 1

                # FAILED WINDOW
                if is_failed:
                    state["failed_window"].append(now)

                    while state["failed_window"]:
                        diff = (now - state["failed_window"][0]).total_seconds()
                        if diff > TIME_WINDOW_SECONDS:
                            state["failed_window"].popleft()
                        else:
                            break

                # RULE DETECTION
                anomalies = []
                correlations = []

                # 1-2 line security risks (Heuristics)
                if len(state["failed_window"]) >= THRESHOLD:
                    anomalies.append({"type": "brute_force", "risk": "high", "message": "Multiple failed logins detected"})

                if is_danger or "unauthorized ssh" in log.lower():
                    anomalies.append({
                        "type": "critical_command" if is_danger else "unauthorized_access",
                        "risk": "critical",
                        "message": "Destructive command detected" if is_danger else "Unauthorized SSH attempt"
                    })

                if "base64" in log.lower() and ("key" in log.lower() or "secret" in log.lower()):
                    anomalies.append({"type": "credential_leak", "risk": "critical", "message": "Potential encoded credential detected"})

                if state["attack_active"] and is_success:
                    correlations.append({"type": "account_compromise", "risk": "critical"})

                # ML DETECTION (Isolation Forest)
                features = build_features(state, is_failed, is_success, is_danger, now)
                
                # Warmup: collect 100 samples globally before fitting
                if not MODEL_TRAINED:
                    training_samples.append(features[0])
                    if len(training_samples) >= 100:
                        model.fit(np.array(training_samples))
                        MODEL_TRAINED = True
                        logger.info(">>> ML MODEL TRAINED (100 samples reached)")
                    is_anomaly = False
                else:
                    score = model.decision_function(features)[0]
                    is_anomaly = model.predict(features)[0] == -1

                    if is_anomaly:
                        anomalies.append({
                            "type": "ml_anomaly",
                            "risk": "medium",
                            "score": float(score),
                            "message": "Behavioral deviation detected"
                        })

                # ATTACK STATE
                if anomalies or correlations:
                    state["attack_active"] = True
                    state["last_detected"] = now_real

                # BUFFER
                if state["attack_active"] or is_failed or is_success or is_danger:
                    state["attack_buffer"].append(log)

                # PATTERN STORE
                if anomalies:
                    state["pattern_store"].append(1)

                # RESET
                if state["attack_active"]:
                    if now_real - state["last_detected"] > RESET_WINDOW:
                        logger.info(f"Resetting state for {ip}")

                        state["attack_active"] = False
                        state["failed_window"].clear()
                        state["attack_buffer"].clear()
                        state["pattern_store"].clear()

                        state["request_count"] = 0
                        state["success_count"] = 0
                        state["error_count"] = 0

                # STATE DEBUG
                logger.info(f"[STATE] IP={ip} | failed={len(state['failed_window'])} | buffer={len(state['attack_buffer'])} | patterns={len(state['pattern_store'])} | active={state['attack_active']}")

                # RISK
                findings = detect_sensitive_data(log)
                risk_score, risk_level = calculate_risk(findings, anomalies, correlations)

                policy = apply_policy(log, findings, risk_level, {"mask": True})

                if is_danger:
                    policy["action"] = "blocked"

                result = {
                    "ip": ip,
                    "risk_level": risk_level,
                    "anomalies": anomalies,
                    "correlations": correlations,
                    "action": policy["action"],
                    "ai_analysis": {}
                }

                logger.info("FINAL RESULT: %s", result)

                # SAVE EVERY LOG to log_collection (so GET /logs works)
                try:
                    log_collection.insert_one({
                        "ip": ip,
                        "content": log,
                        "risk_level": risk_level,
                        "created_at": datetime.now(timezone.utc)
                    })
                except Exception as e:
                    logger.error(">>> LOG SAVE ERROR: %s", e)

                # SAVE INCIDENT (RULE BASED) — store the inserted_id so AI can update it later
                rule_incident_id = None
                if anomalies or correlations:
                    try:
                        incident = {
                            "ip": ip,
                            "risk_level": risk_level,
                            "severity": "critical" if any(a.get("risk") == "critical" for a in anomalies) else risk_level,
                            "anomalies": anomalies,
                            "correlations": correlations,
                            "logs": state["attack_buffer"][-5:],
                            "ai_analysis": {},
                            "created_at": datetime.now(timezone.utc)
                        }

                        res = incident_collection.insert_one(incident)
                        rule_incident_id = res.inserted_id
                        logger.info(f">>> RULE INCIDENT SAVED | ID={rule_incident_id}")

                    except Exception as e:
                        logger.error(">>> RULE SAVE ERROR: %s", e)

                # AI TRIGGER
                trigger_ai = (
                    len(state["pattern_store"]) >= PATTERN_THRESHOLD
                    or correlations
                    or (is_danger and state["attack_active"])
                )

                logger.info(f"[AI CHECK] trigger={trigger_ai}, cooldown_ok={(now_real - state['last_ai_trigger'] > AI_COOLDOWN)}, buffer_ok={len(state['attack_buffer']) >= 5}")

                # AI CALL
                has_ai_analysis = False
                if (
                    trigger_ai
                    and (now_real - state["last_ai_trigger"] > AI_COOLDOWN)
                    and len(state["attack_buffer"]) >= 5
                ):
                    logger.info(f"AI TRIGGERED for {ip}")

                    state["last_ai_trigger"] = now_real

                    context_logs = state["attack_buffer"][-10:]
                    batch_text = "\n".join(context_logs)

                    try:
                        # Using the service name 'backend' because this is running inside the 'consumer' container
                        response = requests.post(
                            "http://backend:8000/analyze",
                            data={
                                "input_type": "text",
                                "content": batch_text,
                                "options": json.dumps({"mask": True})
                            }
                        )

                        if response.status_code == 200:
                            ai_data = response.json().get("ai_analysis", {})
                            result["ai_analysis"] = ai_data 
                            has_ai_analysis = True

                            logger.info("AI RESULT: %s", ai_data)

                            # UPDATE the existing rule-based incident with AI analysis
                            # instead of creating a duplicate incident
                            if rule_incident_id:
                                incident_collection.update_one(
                                    {"_id": rule_incident_id},
                                    {"$set": {
                                        "ai_analysis": ai_data,
                                        "severity": "critical",
                                        "logs": context_logs,
                                    }}
                                )
                                logger.info(f">>> AI ANALYSIS MERGED INTO INCIDENT {rule_incident_id}")
                            else:
                                # No prior rule incident (edge case) — insert fresh
                                incident_collection.insert_one({
                                    "ip": ip,
                                    "risk_level": risk_level,
                                    "severity": "critical",
                                    "anomalies": anomalies,
                                    "correlations": correlations,
                                    "logs": context_logs,
                                    "ai_analysis": ai_data,
                                    "created_at": datetime.now(timezone.utc)
                                })
                                logger.info(">>> AI INCIDENT SAVED (no prior rule incident)")

                    except Exception as e:
                        logger.error("AI ERROR: %s", e)

                    state["pattern_store"].clear()
                    state["attack_buffer"].clear()

                if redis_client:
                    try:
                        # Create a payload for the frontend, now including AI analysis and a unique ID
                        websocket_payload = {
                            "id": str(uuid.uuid4()),
                            "log": log,
                            "ip": ip,
                            "risk_level": risk_level,
                            "anomalies": anomalies,
                            "correlations": correlations,
                            "action": policy["action"],
                            "ai_analysis": result["ai_analysis"],
                            "timestamp": now.isoformat()
                        }
                        redis_client.publish(LIVE_LOG_CHANNEL, json.dumps(websocket_payload))
                        logger.info(f">>> PUBLISHED TO REDIS: {ip} | risk={risk_level} | AI={'YES' if has_ai_analysis else 'NO'}")
                    except Exception as e:
                        logger.error(f"Redis publish error: %s", e)
         

                state["last_request_time"] = now

            except Exception as e:
                # This will catch errors processing a single message
                logger.error(f"Error processing a single Kafka message: {e}", exc_info=True)

    except Exception as e:
        # This will catch the error that is causing the entire consumer to crash
        logger.critical(f"FATAL ERROR in consumer loop, consumer is crashing: {e}", exc_info=True)
        # Keep the container alive for a moment to ensure logs are sent
        time.sleep(60)
    # --- END FIX ---

# This part is for the run_consumer.py script to call
if __name__ == '__main__':
    start_consumer()