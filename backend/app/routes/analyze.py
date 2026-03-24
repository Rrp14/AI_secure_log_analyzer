from fastapi import APIRouter
from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.detection import detect_sensitive_data
from app.services.risk import calculate_risk

router = APIRouter()

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):

    content = request.content

    # Detection
    findings = detect_sensitive_data(content)

    # Risk
    risk_score, risk_level = calculate_risk(findings)

    # Basic summary
    summary = "Analysis completed"
    if findings:
        summary = "Sensitive data detected in input"

    insights = []
    if risk_level == "high":
        insights.append("High-risk sensitive data found")

    return {
        "summary": summary,
        "findings": findings,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "insights": insights
    }