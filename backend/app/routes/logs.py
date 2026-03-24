from app.services.log_generator import attack_sequence, generate_log
from fastapi import APIRouter

router=APIRouter()

@router.get("/generate-log")
def generate(log_type: str = "mixed"):
    return {"log": generate_log(log_type)}


@router.get("/generate-attack")
def generate_attack():
    return {"logs": attack_sequence()}