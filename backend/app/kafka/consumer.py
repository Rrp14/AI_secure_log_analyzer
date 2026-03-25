import os
from kafka import KafkaConsumer
import json
import requests
import time
import re
from collections import deque, defaultdict
from datetime import datetime, timezone
import uuid
import numpy as np
from sklearn.ensemble import IsolationForest
from dotenv import load_dotenv
import redis

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

def get_kafka_consumer():
    s = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    try:
        c = KafkaConsumer(
            TOPIC,
            bootstrap_servers=s.split(','),
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            group_id="log-group",
            request_timeout_ms=30000
        )
        print(f"Kafka Consumer connected to: {s}")
        return c
    except Exception as e:
        print(f"Failed to connect to Kafka at {s}: {e}")
        exit(1)

consumer = get_kafka_consumer()

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

    print("Kafka Consumer started...")

    for message in consumer:
        try:
            log_data = message.value

            if log_data.get("source") == "ai":
                continue

            log = log_data["log"]
            print("\nReceived:", log)

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
                    print(">>> ML MODEL TRAINED (100 samples reached)")
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
                    print(f"Resetting state for {ip}")

                    state["attack_active"] = False
                    state["failed_window"].clear()
                    state["attack_buffer"].clear()
                    state["pattern_store"].clear()

                    state["request_count"] = 0
                    state["success_count"] = 0
                    state["error_count"] = 0

            # STATE DEBUG
            print(f"[STATE] IP={ip} | failed={len(state['failed_window'])} | buffer={len(state['attack_buffer'])} | patterns={len(state['pattern_store'])} | active={state['attack_active']}")

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

            print("FINAL RESULT:", result)

            # SAVE EVERY LOG to log_collection (so GET /logs works)
            try:
                log_collection.insert_one({
                    "ip": ip,
                    "content": log,
                    "risk_level": risk_level,
                    "created_at": datetime.now(timezone.utc)
                })
            except Exception as e:
                print(">>> LOG SAVE ERROR:", e)

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
                    print(f">>> RULE INCIDENT SAVED | ID={rule_incident_id}")

                except Exception as e:
                    print(">>> RULE SAVE ERROR:", e)

            # AI TRIGGER
            trigger_ai = (
                len(state["pattern_store"]) >= PATTERN_THRESHOLD
                or correlations
                or (is_danger and state["attack_active"])
            )

            print(f"[AI CHECK] trigger={trigger_ai}, cooldown_ok={(now_real - state['last_ai_trigger'] > AI_COOLDOWN)}, buffer_ok={len(state['attack_buffer']) >= 5}")

            # AI CALL
            has_ai_analysis = False
            if (
                trigger_ai
                and (now_real - state["last_ai_trigger"] > AI_COOLDOWN)
                and len(state["attack_buffer"]) >= 5
            ):
                print(f"AI TRIGGERED for {ip}")

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

                        print("AI RESULT:", ai_data)

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
                            print(f">>> AI ANALYSIS MERGED INTO INCIDENT {rule_incident_id}")
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
                            print(">>> AI INCIDENT SAVED (no prior rule incident)")

                except Exception as e:
                    print("AI ERROR:", e)

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
                    print(f">>> PUBLISHED TO REDIS: {ip} | risk={risk_level} | AI={'YES' if has_ai_analysis else 'NO'}")
                except Exception as e:
                    print(f"Redis publish error: {e}")
         

            state["last_request_time"] = now

        except Exception as e:
            print("Consumer error:", e)


if __name__ == "__main__":
    start_consumer()