import threading
import time
import logging
from app.kafka.producer import start_producer

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging.info("Producer runner script started.")
    
    # A threading.Event is used to signal stopping
    stop_event = threading.Event()
    
    try:
        # This will start the main loop inside producer.py
        start_producer(stop_event)
    except KeyboardInterrupt:
        logging.info("Shutting down producer...")
        stop_event.set()
    except Exception as e:
        logging.error(f"Producer runner failed: {e}", exc_info=True)
        stop_event.set()
