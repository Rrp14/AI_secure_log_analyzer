# AI Secure Log Analyzer - Backend

A FastAPI-based backend for analyzing logs, detecting security anomalies, performing risk assessment, and providing real-time insights using AI and machine learning.

## Features

- **Log Analysis**: Parse and analyze logs from text input or file uploads.
- **Sensitive Data Detection**: Identify passwords, API keys, credit card numbers, and PII.
- **Risk Scoring**: Calculate risk levels based on detected findings and anomalies.
- **Anomaly Detection**: ML-based detection using Isolation Forest.
- **Brute Force Detection**: Detect brute force attacks within time windows.
- **Correlation Detection**: Identify attack patterns and account compromises.
- **AI-Powered Insights**: Generate detailed analysis using Google Generative AI (Gemini).
- **Real-Time WebSocket Feed**: Live streaming of log analysis results.
- **Producer Control**: Start/stop a continuous stream of logs for live demos via API.
- **Rate Limiting**: Redis-backed rate limiting (5 requests/minute).
- **MongoDB Storage**: Persist incidents and analysis results.
- **Kafka Integration**: Stream logs for continuous processing and anomaly detection.
- **Dockerized Deployment**: Fully containerized with Docker for easy setup and deployment.

## Tech Stack

- **Framework**: FastAPI
- **Database**: MongoDB (MongoDB Atlas recommended)
- **Cache/Pub-Sub**: Redis
- **Message Queue**: Kafka
- **ML Library**: Scikit-learn (Isolation Forest)
- **AI Model**: Google Generative AI
- **Testing**: Pytest
- **Containerization**: Docker & Docker Compose

## Setup (Docker - Recommended)

This is the easiest and recommended way to run the entire application stack.

### Prerequisites

- Docker & Docker Compose
- Git
- MongoDB Atlas Account (for the connection string)
- Google Generative AI API Key

### Installation & Running

1.  **Clone the repository**:
    ```bash
    git clone <your-repo-url>
    cd <your-repo-name>/backend
    ```

2.  **Create `.env` file**: Create a file named `.env` in the `backend` directory and add your secrets.
    ```env
    # .env
    MONGO_URI="mongodb+srv://<user>:<password>@<atlas-cluster-url>/?retryWrites=true&w=majority"
    GEMINI_API_KEY="your-gemini-api-key"
    ```

3.  **Build and Run with Docker Compose**: This single command will build the Docker images and start all services (FastAPI backend, Kafka consumer, Kafka, Zookeeper, and Redis).
    ```bash
    docker-compose up --build -d
    ```

4.  **Verify Services**: Check that all containers are running.
    ```bash
    docker-compose ps
    ```
    You should see `backend_server`, `kafka_consumer`, `kafka`, `zookeeper`, and `redis` with a status of `Up`.

5.  **Access the API**: The backend is now running at `http://localhost:8000`.
    - **Swagger UI**: `http://localhost:8000/docs`
    - **ReDoc**: `http://localhost:8000/redoc`

### Stopping the Application

```bash
docker-compose down
```

---

## Setup (Manual - For Development)

### Prerequisites

- Python 3.10+
- Redis, MongoDB, and Kafka running on their default ports.
- Google Generative AI API Key

### Installation

1.  **Clone the repository** and navigate to the `backend` directory.

2.  **Create a virtual environment**:
    ```bash
    python -m venv .venv
    .venv\Scripts\activate  # Windows
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure environment variables** (create `.env`):
    ```env
    MONGO_URI=mongodb+srv://<user>:<password>@<atlas-cluster-url>/
    GEMINI_API_KEY=your_gemini_api_key_here
    REDIS_URL=redis://localhost:6379/0
    ```

### Running the Services

1.  **Start the FastAPI Server**:
    ```bash
    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
    ```

2.  **Start the Kafka Consumer** (in a separate terminal):
    ```bash
    python -m app.kafka.consumer
    ```

---

## Testing

### Run All Tests

```bash
pytest -q
```

### Run Specific Test File

```bash
pytest tests/test_analyze_endpoint.py -v
```

**Note**: Tests override the rate limiter dependency to avoid requiring Redis initialization during test execution.

---

## API Endpoints

### 1. Producer Control (For Live Demo)

#### Start Producer

**Endpoint**: `POST /producer/start`
**Description**: Starts a background thread that continuously generates logs and sends them to Kafka.
```bash
curl -X POST "http://127.0.0.1:8000/producer/start"
```

#### Stop Producer

**Endpoint**: `POST /producer/stop`
**Description**: Stops the background log generation thread.
```bash
curl -X POST "http://127.0.0.1:8000/producer/stop"
```

#### Get Producer Status

**Endpoint**: `GET /producer/status`
**Description**: Checks if the producer is currently running.
```bash
curl "http://127.0.0.1:8000/producer/status"
```

---

### 2. Analyze Logs/Text

**Endpoint**: `POST /analyze`
**Description**: On-demand analysis of a block of text or a log file.
```bash
curl -X POST "http://127.0.0.1:8000/analyze" \
  -F "input_type=text" \
  -F "content=user=admin password=secret123"
```

---

### 3. Fetch Incidents

**Endpoint**: `GET /incidents`
**Description**: Retrieve stored security incidents from the database.
```bash
curl "http://127.0.0.1:8000/incidents?limit=10"
```

---

### 4. Fetch Logs

**Endpoint**: `GET /logs`
**Description**: Retrieve historical logs from the database.
```bash
curl "http://127.0.0.1:8000/logs?limit=20&ip=192.168.1.100"
```

---

## WebSocket - Real-Time Log Analysis

**Endpoint**: `WS /ws/live_logs`
**Description**: Connect to receive real-time analysis results as logs are processed by the Kafka consumer.

---

## Frontend Integration Guide

### Overview

Your frontend should:
1.  Connect to the WebSocket for live analysis updates.
2.  Call `/producer/start` and `/producer/stop` to control the live demo.
3.  Call `/analyze` for on-demand log analysis.
4.  Fetch `/incidents` and `/logs` for historical data.

### 1. Control the Live Demo

Your frontend can use buttons to call these endpoints and control the flow of logs for the live demo.

```javascript
// Example functions to control the log producer

async function startLiveDemo() {
  await fetch('http://127.0.0.1:8000/producer/start', { method: 'POST' });
  console.log("Live demo started.");
}

async function stopLiveDemo() {
  await fetch('http://127.0.0.1:8000/producer/stop', { method: 'POST' });
  console.log("Live demo stopped.");
}

async function checkDemoStatus() {
  const response = await fetch('http://127.0.0.1:8000/producer/status');
  const data = await response.json();
  console.log("Producer status:", data.status); // "running" or "stopped"
  return data.status;
}
```

### 2. Live Log Analysis (WebSocket)

(Your existing WebSocket guide is perfect here)

### 3. On-Demand Analysis (`/analyze`)

(Your existing `/analyze` guide is perfect here)

### 4. Fetch Incidents and Logs

(Your existing `/incidents` and `/logs` guides are perfect here)

---

## Deployment Guide: Azure VM

Using a virtual machine is a great way to deploy this application, as it gives you full control and works seamlessly with Docker Compose.

### Prerequisites

- An Azure account with an active subscription.
- An Azure VM (e.g., Standard B2s - 2 vCPUs, 4GiB memory) running Ubuntu.
- SSH access to your VM.

### Step 1: Prepare the VM

Connect to your VM via SSH and install the necessary tools.

```bash
# Update package lists
sudo apt-get update

# Install Docker, Docker Compose, and Git
sudo apt-get install -y docker.io docker-compose git

# Add your user to the Docker group to run commands without sudo
sudo usermod -aG docker $USER

# IMPORTANT: Log out and log back in for the group change to take effect.
exit
```

### Step 2: Deploy the Application

After logging back into your VM:

```bash
# Clone your repository
git clone https://your-repo-url.git
cd <your-repo-name>/backend

# Create the .env file with your production secrets
nano .env
```

Paste your `MONGO_URI` and `GEMINI_API_KEY` into the `.env` file and save it.

```bash
# Build and run all services in the background
docker-compose up --build -d
```

### Step 3: Configure Azure Firewall

By default, your VM will block traffic. You need to open port 8000.

1.  In the Azure Portal, navigate to your Virtual Machine.
2.  Go to the **Networking** settings page.
3.  Click **Add inbound port rule**.
4.  Set the following:
    - **Destination port ranges**: `8000`
    - **Protocol**: `TCP`
    - **Action**: `Allow`
    - **Name**: `Allow-HTTP-8000`
5.  Click **Add**.

### Step 4: Access Your Application

Your application is now live! You can access it at `http://<your-vm-public-ip>:8000`.

---

(The rest of your original README, including Troubleshooting, License, etc., can remain as is.)