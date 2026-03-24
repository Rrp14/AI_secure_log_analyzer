from fastapi import APIRouter
from app.models.db import incident_collection

router = APIRouter()


@router.get("/incidents")
def get_incidents():
    incidents = list(incident_collection.find({}, {"_id": 0}).sort("created_at", -1))
    return {"count": len(incidents), "data": incidents}


@router.get("/incidents/{ip}")
def get_incidents_by_ip(ip: str):
    incidents = list(
        incident_collection.find({"ip": ip}, {"_id": 0}).sort("created_at", -1)
    )
    return {"count": len(incidents), "data": incidents}