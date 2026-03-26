# filepath: c:\Users\Rahul\OneDrive\Desktop\code\AI_secure_log_analyzer\backend\run_consumer.py
import logging
from app.kafka.consumer import start_consumer

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Consumer runner script started.")
    start_consumer()
