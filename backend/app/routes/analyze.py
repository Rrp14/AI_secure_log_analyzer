from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from fastapi_limiter.depends import RateLimiter

from app.models.schemas import AnalyzeResponse
from app.services.detection import detect_sensitive_data
from app.services.risk import calculate_risk
from app.services.ai import analyze_with_ai
from app.services.anomaly import detect_anomalies
from app.services.correlation import detect_correlations
from app.services.input_handler import normalize_input
from app.services.log_parser import parse_logs
from app.services.policy import apply_policy

import json
import logging
import asyncio
import numpy as np

router = APIRouter()
logger = logging.getLogger(__name__)

CHUNK_SIZE = 500
STREAM_CHUNK_BYTES = 1024 * 1024  # 1MB
LARGE_FILE_THRESHOLD = 5 * 1024 * 1024  # 5MB
MAX_AI_LINES = 200


# -------------------------
# HELPERS
# -------------------------
def map_content_type(input_type):
    if input_type in ["log", "file"]:
        return "logs"
    elif input_type == "sql":
        return "sql"
    elif input_type == "chat":
        return "chat"
    return "text"


async def stream_file_lines(file: UploadFile):
    while True:
        chunk = await file.read(STREAM_CHUNK_BYTES)
        if not chunk:
            break
        yield chunk.decode("utf-8", errors="ignore")


def extract_context(lines, findings, window=2):
    context_blocks = []

    for f in findings[:MAX_AI_LINES]:
        idx = f["line"] - 1
        start = max(0, idx - window)
        end = min(len(lines), idx + window + 1)

        snippet = "\n".join(lines[start:end])

        context_blocks.append({
            "type": f["type"],
            "line": f["line"],
            "snippet": snippet
        })

    return context_blocks


# -------------------------
# MAIN ROUTE
# -------------------------
@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    dependencies=[Depends(RateLimiter(5, 60))]  # 5 req / 60 sec
)
async def analyze(
    input_type: str = Form(...),
    content: str = Form(None),
    file: UploadFile = File(None),
    options: str = Form(None)
):
    # -------------------------
    # OPTIONS PARSING (FIXED)
    # -------------------------
    try:
        options_dict = json.loads(options) if options else {}
    except:
        options_dict = {}

    findings = []
    buffer = []
    line_number = 0
    sample_lines = []

    is_large_file = False
    normalized_text = ""

    # -------------------------
    # FILE SIZE CHECK
    # -------------------------
    if file:
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > LARGE_FILE_THRESHOLD:
            is_large_file = True
            logger.info(f"Large file → STREAM MODE")

    # -------------------------
    # STREAM MODE (LARGE FILE)
    # -------------------------
    if is_large_file:
        async for chunk in stream_file_lines(file):
            lines = chunk.split("\n")

            for line in lines:
                buffer.append(line)
                line_number += 1

                if len(sample_lines) < MAX_AI_LINES:
                    sample_lines.append(line)

                if len(buffer) >= CHUNK_SIZE:
                    findings.extend(
                        detect_sensitive_data(
                            "\n".join(buffer),
                            start_line=max(1, line_number - len(buffer) + 1)
                        )
                    )
                    buffer = []

        if buffer:
            findings.extend(
                detect_sensitive_data(
                    "\n".join(buffer),
                    start_line=max(1, line_number - len(buffer) + 1)
                )
            )

        parsed_logs = []
        anomalies = detect_anomalies("\n".join(sample_lines))
        correlations = detect_correlations("\n".join(sample_lines))
        context_data = [{"snippet": "\n".join(sample_lines)}]

        policy_text = "\n".join(sample_lines)

    # -------------------------
    # NORMAL MODE
    # -------------------------
    else:
        normalized_text = await normalize_input(input_type, content, file)

        if not normalized_text:
            raise HTTPException(status_code=400, detail="Invalid input")

        raw_lines = normalized_text.split("\n")
        parsed_logs = parse_logs(raw_lines)

        # fallback if parser fails
        if not parsed_logs:
            parsed_logs = [{"line": i + 1, "message": line} for i, line in enumerate(raw_lines)]

        lines = [log["message"] for log in parsed_logs]

        for i, line in enumerate(lines, start=1):
            buffer.append(line)
            line_number += 1

            if len(buffer) >= CHUNK_SIZE:
                findings.extend(
                    detect_sensitive_data(
                        "\n".join(buffer),
                        start_line=max(1, line_number - len(buffer) + 1)
                    )
                )
                buffer = []

        if buffer:
            findings.extend(
                detect_sensitive_data(
                    "\n".join(buffer),
                    start_line=max(1, line_number - len(buffer) + 1)
                )
            )

        context_data = extract_context(lines, findings)

        partial_text = normalized_text[:20000]
        anomalies = detect_anomalies(partial_text)
        correlations = detect_correlations(partial_text)

        policy_text = "\n".join(lines)

    # -------------------------
    # LIGHTWEIGHT ML SIGNAL
    # -------------------------
    feature_vector = np.array([
        len(findings),
        len(anomalies),
        len(correlations)
    ])

    ml_flag = np.mean(feature_vector) > 5

    # -------------------------
    # RISK ENGINE
    # -------------------------
    risk_score, risk_level = calculate_risk(findings, anomalies, correlations)

    # -------------------------
    # POLICY ENGINE
    # -------------------------
    policy_result = apply_policy(
        policy_text,
        findings,
        risk_level,
        options_dict
    )

    # -------------------------
    # SMART AI TRIGGER (KEY 🔥)
    # -------------------------
    should_call_ai = False

    HIGH_RISK = ["high", "critical"]

    if any(f["risk"] in HIGH_RISK for f in findings):
        should_call_ai = True

    if len(findings) >= 3:
        should_call_ai = True

    if correlations:
        should_call_ai = True

    if ml_flag:
        should_call_ai = True

    # avoid trivial cases
    if len(findings) == 1 and risk_level == "low":
        should_call_ai = False

    if len(policy_text) < 50:
        should_call_ai = False

    # -------------------------
    # SUMMARY
    # -------------------------
    summary = ""

    # -------------------------
    # INSIGHTS (FIXED LOGIC)
    # -------------------------
    insights = []

    # High severity findings
    if any(f["risk"] == "critical" for f in findings):
        insights.append("Critical sensitive data exposed")

    elif any(f["risk"] == "high" for f in findings):
        insights.append("High-risk sensitive data detected")

    # Medium / low fallback
    elif findings:
        insights.append("Sensitive data detected")

    # Anomaly signals
    if anomalies:
        insights.append("Suspicious activity detected")

    # Correlation signals
    if correlations:
        insights.append("Multi-stage attack pattern detected")

    # ML signal
    if ml_flag:
        insights.append("Unusual behavior detected by ML")

    # Final fallback
    if not insights:
        insights.append("No significant risks detected")


    # -------------------------
    # AI MODULE (CONTROLLED)
    # -------------------------
    ai_output = {
        "summary": "Skipped for performance",
        "risks": [],
        "root_cause": "",
        "attack_narrative": ""
    }

    if should_call_ai and not is_large_file:
        try:
            ai_output = await asyncio.to_thread(
                analyze_with_ai,
                context_data,
                findings[:MAX_AI_LINES]
            )
        except:
            ai_output["summary"] = "AI failed"

    # -------------------------
    # FINAL RESPONSE
    # -------------------------
    return {
        "summary": summary,
        "content_type": map_content_type(input_type),
        "findings": findings,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "insights": insights,
        "action": policy_result["action"],
        "ai_analysis": ai_output,
        "anomalies": anomalies,
        "correlations": correlations,
        "parsed_logs": parsed_logs[:20] if options_dict.get("include_parsed") else [],
        "masked_output": (
            policy_result["masked_text"][:500]
            if options_dict.get("include_masked") or options_dict.get("mask")
            else None
        )
    }