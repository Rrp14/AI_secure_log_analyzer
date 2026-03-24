from fastapi import FastAPI
from app.routes.analyze import router as analyze_router
from app.routes.logs import router as log_router
from app.routes.incidents import router as incident_router

import os
from dotenv import load_dotenv
import redis.asyncio as aioredis
from fastapi_limiter import FastAPILimiter
from contextlib import asynccontextmanager

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")



@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = None

    try:
        print("Connecting to Redis...")
        redis_client = aioredis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )

        # ✅ Test connection
        await redis_client.ping()
        print("Redis connected successfully")

        # ✅ Init limiter
        await FastAPILimiter.init(redis_client)

    except Exception as e:
        print("Redis connection failed → continuing without limiter")
        print("Error:", e)

    try:
        yield

    finally:
        if redis_client:
            await redis_client.close()
            print("Redis connection closed")


app = FastAPI(
    title="AI Secure Data Intelligence Platform",
    lifespan=lifespan
)

# Routers
app.include_router(analyze_router)
app.include_router(log_router)
app.include_router(incident_router)


@app.get("/")
def root():
    return {"message": "Backend running !!"}