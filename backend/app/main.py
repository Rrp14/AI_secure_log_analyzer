from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.analyze import router as analyze_router
from app.routes.logs import router as log_router
from app.routes.incidents import router as incident_router
from app.routes.websockets import router as websocket_router

import os
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
import redis.asyncio as aioredis
from fastapi_limiter import FastAPILimiter

load_dotenv()
logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")



@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = None

    try:
        logger.info(f"Connecting to Redis at {REDIS_URL}...")
        redis_client = aioredis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

        # Ensure connection works
        await redis_client.ping()
        await FastAPILimiter.init(redis_client)
        logger.info("FastAPILimiter initialized with Redis")

    except Exception as e:
        logger.error(f"Failed to initialize FastAPILimiter: {e}")

    try:
        yield

    finally:
        if redis_client:
            try:
                await redis_client.close()
            except Exception:
                pass


app = FastAPI(
    title="AI Secure Data Intelligence Platform",
    lifespan=lifespan,
)

# --- CORS MIDDLEWARE ---
# List of allowed origins. Add your deployed frontend URL here.
origins = [
    "http://localhost",
    "http://localhost:3000",  # For React development
    "http://localhost:5173",  # For Vite/React development
    "http://localhost:8080",  # For Vue development
    "http://localhost:4200",  # For Angular development
    "https://<YOUR_DEPLOYED_FRONTEND_URL>", # Placeholder for your production frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)
# --- END CORS MIDDLEWARE ---


# Routers
app.include_router(analyze_router)
app.include_router(log_router)
app.include_router(incident_router)
app.include_router(websocket_router) 



@app.get("/")
def root():
    return {"message": "Backend running !!"}