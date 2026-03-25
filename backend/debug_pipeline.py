import os
import json
import redis
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable
import time

def test_redis():
    print("--- Testing Redis ---")
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        r.ping()
        print("[OK] Redis is reachable on localhost:6379")
        return r
    except Exception as e:
        print(f"[ERROR] Redis unreachable: {e}")
        return None

def test_kafka():
    print("\n--- Testing Kafka ---")
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    try:
        producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers.split(','),
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            request_timeout_ms=2000
        )
        print(f"[OK] Kafka Producer connected to {bootstrap_servers}")
        producer.send("logs_topic", {"test": "connection", "timestamp": time.time()})
        print("[OK] Test message sent to 'logs_topic'")
        return True
    except NoBrokersAvailable:
        print(f"[ERROR] Kafka broker NOT available at {bootstrap_servers}")
        return False
    except Exception as e:
        print(f"[ERROR] Kafka error: {e}")
        return False

def monitor_live_logs():
    print("\n--- Monitoring Live Redis Channel ---")
    r = test_redis()
    if not r: return
    
    pubsub = r.pubsub()
    pubsub.subscribe("live_log_analysis")
    print("Subscribed to 'live_log_analysis'. Waiting for logs (Press Ctrl+C to stop)...")
    try:
        for message in pubsub.listen():
            if message['type'] == 'message':
                print(f"[NEW LOG] {message['data']}")
    except KeyboardInterrupt:
        print("\nStopping monitor.")

if __name__ == "__main__":
    if test_kafka():
        monitor_live_logs()
