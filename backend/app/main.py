from fastapi import FastAPI
from app.routes.analyze import router as analyze_router
from app.routes.logs import router as log_router
from app.routes.incidents import router as incident_router

app = FastAPI(title="AI Secure Data Intelligence Platform")

app.include_router(analyze_router)
app.include_router(log_router)
app.include_router(incident_router)

@app.get("/")
def root():
    return {"message": "Backend running 🚀"}