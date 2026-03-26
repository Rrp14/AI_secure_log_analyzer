#!/bin/bash
echo "Starting Uvicorn server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

echo "Waiting for Kafka broker to be ready at kafka:29092..."
while ! nc -z kafka 29092; do
  sleep 1
done
echo "Kafka broker is ready."

echo "Starting Kafka consumer..."
python run_consumer.py