import os

# Disable FastAPI-Limiter during tests to avoid needing Redis init
os.environ.setdefault("DISABLE_RATE_LIMIT", "1")