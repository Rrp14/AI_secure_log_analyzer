
---

# AI-Powered Secure Log Analyzer

## System Explanation

This system is a **real-time security intelligence platform** designed to process, analyze, and interpret large volumes of log data as they are generated. It combines **event-driven architecture, rule-based detection, machine learning, and generative AI** to transform raw logs into meaningful security insights.

Instead of treating logs as isolated events, the system continuously monitors streams of data, identifies suspicious behavior patterns, correlates related activities, and generates **context-aware security incidents**. These incidents are enriched with AI-generated explanations, enabling faster understanding and response.

From a system design perspective, it follows a **distributed pipeline model**:

* Logs are ingested continuously
* Processed asynchronously
* Analyzed using multiple detection layers
* Converted into structured intelligence
* Delivered in real time to users

This approach ensures:

* **Scalability** → handles high log volume (even GB-scale files)
* **Low latency** → near real-time detection
* **Modularity** → each component works independently
* **Resilience** → failures don’t break the entire system

---

# System Architecture (Diagram Prompt Explanation)

👉 Use this section as a prompt for AI diagram generation.

---

### 🎯 Diagram Prompt (Structured)




# How the System Works (Simplified Flow)

### 1. Log Generation

Logs are continuously generated from applications or simulated using a producer.

---

### 2. Streaming via Kafka

All logs are pushed into Kafka, which acts as a **buffer and pipeline**, allowing independent processing.

---

### 3. Real-Time Processing

The consumer reads logs and runs them through multiple detection layers:

* **Rules** → known attacks (brute force, destructive commands)
* **ML** → unknown anomalies
* **Regex scanning** → sensitive data leaks

---

### 4. Risk Evaluation

Each log is assigned:

* Risk score
* Severity level (low → critical)

---

### 5. Correlation & Incident Creation

Logs are grouped into incidents when:

* Multiple related events occur
* Attack patterns are detected

---

### 6. AI Analysis (Smart Layer)

When a meaningful pattern is detected:

* Logs are sent to AI
* AI generates:

  * Summary
  * Explanation
  * Root cause

---

### 7. Data Storage

All incidents and AI insights are stored in MongoDB.

---

### 8. Real-Time Updates

Processed logs are pushed via Redis → WebSocket → Frontend.

---

### 9. Frontend Visualization

Users see:

* Live logs (streaming)
* Security incidents (with AI summaries)

---

# 🧠 Key Design Highlights (Good for Interview)

* **Hybrid Detection System**

  * Rule-based + ML + AI → covers known + unknown threats

* **Event-Driven Architecture**

  * Kafka ensures scalability and decoupling

* **Streaming + Batch Hybrid**

  * Handles both real-time logs and large file uploads (1GB+)

* **AI-on-Demand**

  * AI is triggered only when meaningful → saves cost

* **Stateful Detection**

  * Tracks behavior per IP → enables correlation

---



## Local Setup and Deployment Guide

Follow these steps to run the entire platform on your local machine using Docker.

### Prerequisites

*   **Docker** and **Docker Compose**: Ensure they are installed and running on your system.
*   **Git**: For cloning the repository.
*   **Web Browser**: For viewing the frontend.

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd AI_secure_log_analyzer
```

### 2. Create Environment File

The application uses environment variables for configuration. Create a `.env` file in the project's root directory. You can copy the example file if one is provided, or create a new one and add the following content:

```env
# .env

# Kafka Configuration
KAFKA_TOPIC=secure_logs
KAFKA_BOOTSTRAP_SERVERS=kafka:29092

# Redis Configuration
REDIS_URL=redis://redis:6379/0

GEMINI_API_KEY=add_your key

# MongoDB Configuration
MONGO_INITDB_ROOT_USERNAME=mongoadmin
MONGO_INITDB_ROOT_PASSWORD=secret
MONGO_URI=mongodb://mongoadmin:secret@mongo:27017/

# API Configuration (used by Next.js to talk to FastAPI)
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8000
```

### 3. Build and Run the Application

The `docker-compose.yml` file is configured to build all the services (frontend, backend, Kafka, Zookeeper, Redis, MongoDB) and run them in the correct order.

Open a terminal in the project's root directory and run:

```bash
docker-compose up --build
```

*   `--build`: This flag tells Docker Compose to build the images from the Dockerfiles the first time you run it (or if you've made changes to the code or Dockerfiles).
*   You can omit `--build` on subsequent runs to start the containers faster.
*   To run in the background, use `docker-compose up -d --build`.

### 4. Accessing the Application

Once the containers are up and running (this may take a minute or two, especially on the first run as Kafka initializes), you can access the different parts of the system:

*   **Main Web Interface**: Open your browser and navigate to **`http://localhost:3000`**
    *   The **Dashboard** will show incidents as they are created.
    *   The **Live Demo** page will show the real-time stream of all processed logs.

### 5. How to See it in Action

1.  Navigate to the **Live Demo** page at `http://localhost:3000/live`. You will see a stream of logs being processed.
2.  Wait for an attack sequence to be triggered by the producer (you will see messages like "BRUTE FORCE ATTACK SEQUENCE TRIGGERED" in your terminal).
3.  Observe the live feed as a cluster of `HIGH` and `CRITICAL` logs appear for the same IP address.
4.  Navigate back to the **Dashboard** at `http://localhost:3000`. A new incident will have appeared.
5.  Click on the incident to expand it. After a few moments, the "AI Analysis" section will populate with a summary of the attack.

### 6. Stopping the Application

To stop all running containers, press `Ctrl + C` in the terminal where `docker-compose` is running.

If you are running in detached mode, use the following command:

```bash
docker-compose down
```
```
