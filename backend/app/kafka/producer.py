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

# Attack control
last_attack_time = 0
ATTACK_COOLDOWN = 60  # seconds

# Traffic behavior
NORMAL_SLEEP_RANGE = (1, 3)   # seconds
BURST_MODE_PROB = 0.2         # 20% chance of burst
BURST_COUNT_RANGE = (3, 6)    # logs in burst


def send_log(log):
    producer.send(TOPIC, {"log": log})
    print("Sent:", log)


def start_producer():
    global last_attack_time

    print("Kafka Producer started...")

    while True:
        try:
            current_time = time.time()
            r = random.random()

            # -------------------------
            # Attack trigger (controlled)
            # -------------------------
            if (current_time - last_attack_time > ATTACK_COOLDOWN) and (r < 0.08):

                print("\nATTACK SEQUENCE TRIGGERED\n")

                logs = attack_sequence()

                for log in logs:
                    send_log(log)
                    time.sleep(1)

                last_attack_time = time.time()
                continue  # skip normal flow after attack

            # -------------------------
            # Normal / burst traffic
            # -------------------------
            if random.random() < BURST_MODE_PROB:
                burst_count = random.randint(*BURST_COUNT_RANGE)

                for _ in range(burst_count):
                    log = generate_log()
                    send_log(log)

                # short pause after burst
                time.sleep(random.uniform(1, 2))

            else:
                log = generate_log()
                send_log(log)

                time.sleep(random.uniform(*NORMAL_SLEEP_RANGE))

        except Exception as e:
            print("Producer error:", e)


if __name__ == "__main__":
    start_producer()