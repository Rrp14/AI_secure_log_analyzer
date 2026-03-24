from kafka import KafkaProducer
import json
import time
import random

from app.services.log_generator import generate_log, attack_sequence

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

TOPIC = "logs_topic"


def start_producer():
    print("Kafka Producer started...")

    while True:
        try:
            # 🔥 20% chance → attack simulation
            if random.random() < 0.2:
                logs = attack_sequence()
                print("\n⚠ Sending ATTACK sequence")

                for log in logs:
                    producer.send(TOPIC, {"log": log})
                    print("Sent:", log)
                    time.sleep(1)

            else:
                log = generate_log("mixed")
                producer.send(TOPIC, {"log": log})
                print("Sent:", log)

            time.sleep(2)

        except Exception as e:
            print("Producer error:", e)


if __name__ == "__main__":
    start_producer()