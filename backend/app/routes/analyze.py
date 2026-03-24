from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from app.models.schemas import AnalyzeResponse
from app.services.detection import detect_sensitive_data
from app.services.risk import calculate_risk
from app.services.ai import analyze_with_ai
from app.services.anomaly import detect_anomalies
from app.services.correlation import detect_correlations
from app.services.input_handler import normalize_input
from app.services.log_parser import parse_logs
from app.services.policy import apply_policy
import ast
import logging
import asyncio
import json

router = APIRouter()
logger = logging.getLogger(__name__)

CHUNK_SIZE = 500


# Context extraction
def extract_context(lines, findings, window=2):
    context_blocks = []

    for f in findings:
        line_index = f["line"] - 1

        start = max(0, line_index - window)
        end = min(len(lines), line_index + window + 1)

        snippet = "\n".join(lines[start:end])

        context_blocks.append({
            "type": f["type"],
            "line": f["line"],
            "snippet": snippet
        })

    return context_blocks


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    input_type: str = Form(...),
    content: str = Form(None),
    file: UploadFile = File(None),
    options: str = Form(None)   
):
    # Parse options


    try:
      if options:
        options_dict = ast.literal_eval(options)
      else:
        options_dict = {}
    except Exception as e:
      print("OPTIONS ERROR:", e)
      options_dict = {}

    

    #Normalize input
    normalized_text = await normalize_input(input_type, content, file)

    if not normalized_text:
        raise HTTPException(status_code=400, detail="Invalid or empty input")

    decoded_content = normalized_text
    raw_lines = decoded_content.split("\n")

    #Structured parsing
    parsed_logs = parse_logs(raw_lines)

    #Use only message for detection
    lines = [log["message"] for log in parsed_logs]

    findings = []
    buffer = []
    line_number = 0

    logger.info(f"Processing input type: {input_type}")

    #Chunk processing
    for i, line in enumerate(lines, start=1):
        buffer.append(line)
        line_number += 1

        if len(buffer) >= CHUNK_SIZE:
            chunk_text = "\n".join(buffer)
            current_line = line_number - len(buffer) + 1

            findings.extend(
                detect_sensitive_data(chunk_text, start_line=current_line)
            )
            buffer = []

    # Remaining buffer
    if buffer:
        chunk_text = "\n".join(buffer)
        current_line = line_number - len(buffer) + 1

        findings.extend(
            detect_sensitive_data(chunk_text, start_line=current_line)
        )

    if line_number == 0:
        raise HTTPException(status_code=400, detail="Empty input")

    #Context for AI
    context_data = extract_context(lines, findings)

    #Anomaly + Correlation
    partial_text = decoded_content[:20000]
    anomalies = detect_anomalies(partial_text)
    correlations = detect_correlations(partial_text)

    #Risk
    risk_score, risk_level = calculate_risk(findings, anomalies, correlations)

    #POLICY ENGINE (MODE 1)
    policy_result = apply_policy(
        decoded_content,
        findings,
        risk_level,
        options_dict
    )

    #Summary
    if findings:
        summary = f"{len(findings)} sensitive findings detected. Risk level: {risk_level.upper()}"
    else:
        summary = "No sensitive data detected"

    #Insights
    insights = []

    if anomalies:
        insights.append("Suspicious activity detected (possible brute-force attack)")

    if correlations:
        insights.append("Multi-stage attack pattern detected")

    if any(f["risk"] in ["high", "critical"] for f in findings):
        insights.append("Sensitive data exposure detected")

    if not insights:
        insights.append("No major risks detected")

    logger.info(f"Findings count: {len(findings)} | Risk: {risk_level}")

    # AI Analysis
    if findings:
        try:
            ai_output = await asyncio.to_thread(
                analyze_with_ai,
                context_data,
                findings
            )
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

    return {
        "summary": summary,
        "findings": findings,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "insights": insights,
        "ai_analysis": ai_output,
        "anomalies": anomalies,
        "correlations": correlations,
        "parsed_logs": parsed_logs[:20] if options_dict.get("include_parsed", False) else [],
        "action": policy_result["action"],
        "masked_output": policy_result["masked_text"][:500] if options_dict.get("include_masked", False) else None
    }