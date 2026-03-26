FROM python:3.11-slim

WORKDIR /app

# Copy only the backend code
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt


# --- FIX: Use the new start script ---
# Copy and make the start script executable
COPY ./start-producer.sh /app/start-producer.sh
RUN chmod +x /app/start-producer.sh

# Command to run the start script
CMD ["/app/start-producer.sh"]
