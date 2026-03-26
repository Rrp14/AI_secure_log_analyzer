from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.analyze import router as analyze_router
from app.routes.logs import router as log_router
from app.routes.incidents import router as incident_router
from app.routes.websockets import router as websocket_router

import os
import logging
import asyncio
from contextlib import asynccontextmanager

from dotenv import load_dotenv
import redis.asyncio as aioredis
from fastapi_limiter import FastAPILimiter

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# REDIS FALLBACK
def get_redis_url():
    hosts = ["redis", "localhost"]
    for h in hosts:
        try:
            url = f"redis://{h}:6379/0"
   
            return url
        except:
            continue
    return "redis://localhost:6379/0"

REDIS_URL = os.getenv("REDIS_URL", get_redis_url())



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
        # Start the Redis listener for WebSockets
        from app.routes.websockets import redis_listener
        asyncio.create_task(redis_listener())

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)


# Routers
app.include_router(analyze_router,prefix="/api")
app.include_router(log_router,prefix="/api")
app.include_router(incident_router,prefix="/api")
app.include_router(websocket_router,prefix="/api") 


@app.get("/")
def root():
    return {"message": "Backend running !!"}