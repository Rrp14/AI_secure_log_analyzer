from kafka import KafkaProducer
import json
import time
import random
import threading

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
    producer.send(TOPIC, {"log": log, "source": "producer"})
    print("Sent:", log)


def start_producer(stop_event: threading.Event):
    """
    Starts the log producer loop.
    The loop will run until the stop_event is set.
    """
    global last_attack_time
    last_attack_time = 0

    print("Kafka Producer started...")

    while not stop_event.is_set():
        try:
            current_time = time.time()
            r = random.random()

            # Attack trigger (controlled)
            if (current_time - last_attack_time > ATTACK_COOLDOWN) and (r < 0.08):

                print("\nATTACK SEQUENCE TRIGGERED\n")

                logs = attack_sequence()

                for log in logs:
                    send_log(log)
                    time.sleep(1)

                last_attack_time = time.time()
                continue  # skip normal flow after attack

            # Normal / burst traffic
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
    
    print("Kafka Producer stopped.")


if __name__ == "__main__":
    # This part is now just for manual testing
    stop = threading.Event()
    try:
        start_producer(stop)
    except KeyboardInterrupt:
        stop.set()