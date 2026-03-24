from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import AnalyzeResponse
from app.services.detection import detect_sensitive_data
from app.services.risk import calculate_risk
from io import BytesIO
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

CHUNK_SIZE = 500
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/analyze-file", response_model=AnalyzeResponse)
async def analyze_file(file: UploadFile = File(...)):

    if not file.filename.endswith((".txt", ".log")):
        raise HTTPException(status_code=400, detail="Only .txt or .log files allowed")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")

    file.file = BytesIO(contents)

    findings = []
    buffer = []
    line_number = 0

    logger.info(f"Processing file: {file.filename}")

    for line in file.file:

        try:
            decoded_line = line.decode("utf-8")
        except UnicodeDecodeError:
            continue

        buffer.append(decoded_line)
        line_number += 1

        if len(buffer) >= CHUNK_SIZE:
            chunk_text = "".join(buffer)
            current_line = line_number - len(buffer) + 1
            findings.extend(detect_sensitive_data(chunk_text, start_line=current_line))
            buffer = []

    if buffer:
        chunk_text = "".join(buffer)
        current_line = line_number - len(buffer) + 1
        findings.extend(detect_sensitive_data(chunk_text, start_line=current_line))

    if line_number == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    risk_score, risk_level = calculate_risk(findings)

    if findings:
        summary = f"Detected {len(findings)} sensitive items in uploaded file"
    else:
        summary = "No sensitive data detected"

    insights = []
    if risk_level in ["high", "critical"]:
        insights.append("High-risk sensitive data found in file")
    elif risk_level == "medium":
        insights.append("Moderate risk detected")

    await file.close()

    return {
        "summary": summary,
        "findings": findings,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "insights": insights
    }