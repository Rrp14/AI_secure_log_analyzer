from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import AnalyzeResponse
from app.services.detection import detect_sensitive_data
from app.services.risk import calculate_risk
from app.services.ai import analyze_with_ai
from io import BytesIO
import logging
import asyncio

router = APIRouter()
logger = logging.getLogger(__name__)

CHUNK_SIZE = 500
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/analyze-file", response_model=AnalyzeResponse)
async def analyze_file(file: UploadFile = File(...)):

    # ✅ File validation
    if not file.filename.endswith((".txt", ".log")):
        raise HTTPException(status_code=400, detail="Only .txt or .log files allowed")

    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")

    # Reset file pointer
    file.file = BytesIO(contents)

    findings = []
    buffer = []
    line_number = 0

    logger.info(f"Processing file: {file.filename}")

    # ✅ Chunk processing
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
            findings.extend(
                detect_sensitive_data(chunk_text, start_line=current_line)
            )
            buffer = []

    # Remaining buffer
    if buffer:
        chunk_text = "".join(buffer)
        current_line = line_number - len(buffer) + 1
        findings.extend(
            detect_sensitive_data(chunk_text, start_line=current_line)
        )

    if line_number == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    # ✅ Risk calculation
    risk_score, risk_level = calculate_risk(findings)

    # ✅ Summary
    if findings:
        summary = f"{len(findings)} sensitive findings detected. Risk level: {risk_level.upper()}"
    else:
        summary = "No sensitive data detected"

    # ✅ Insights
    insights = []
    if risk_level in ["high", "critical"]:
        insights.append("High-risk sensitive data found in file")
    elif risk_level == "medium":
        insights.append("Moderate risk detected")

    logger.info(f"Findings count: {len(findings)} | Risk: {risk_level}")

    # ✅ AI Analysis (safe + async)
    full_text = contents.decode("utf-8", errors="ignore")

    if findings:
        try:
            ai_output = await asyncio.to_thread(analyze_with_ai, full_text, findings)
        except Exception:
            ai_output = {
                "summary": "AI timeout or failed",
                "risks": [],
                "root_cause": "",
                "attack_narrative": ""
            }
    else:
        ai_output = {
            "summary": "No risks detected",
            "risks": [],
            "root_cause": "",
            "attack_narrative": ""
        }

    await file.close()

    return {
        "summary": summary,
        "findings": findings,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "insights": insights,
        "ai_analysis": ai_output
    }