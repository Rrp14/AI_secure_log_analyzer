#!/bin/bash

# --- Wait for Kafka to be ready ---
echo "Producer: Waiting for Kafka broker to be ready at kafka:29092..."

# Install netcat-openbsd if missing
if ! command -v nc &> /dev/null; then
    echo "Installing netcat..."
    apt-get update && apt-get install -y netcat-openbsd
fi

# Loop until Kafka is reachable
while ! nc -z kafka 29092; do
  echo "Producer: Waiting for Kafka..."
  sleep 2
done

echo "Producer: Kafka broker is ready."

# Start the Producer runner script
# Using -u ensures logs show up in docker logs immediately
echo "Producer: Starting producer runner script..."
python3 -u run_producer.py
