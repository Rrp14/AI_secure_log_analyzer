from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


# -------------------------
# REQUEST
# -------------------------
class AnalyzeRequest(BaseModel):
    input_type: str
    content: str
    options: Optional[Dict[str, Any]] = None


# -------------------------
# FINDINGS
# -------------------------
class Finding(BaseModel):
    type: str
    value: str
    line: int
    risk: str


# -------------------------
# PARSED LOG
# -------------------------
class ParsedLog(BaseModel):
    line: int
    timestamp: Optional[str]
    level: str
    message: str


# -------------------------
# INCIDENT MODEL (FIXED ✅)
# -------------------------
class Incident(BaseModel):
    id: Optional[str] = None
    ip: str
    risk_level: str
    severity: Optional[str] = "medium"
    anomalies: List[Dict[str, Any]]
    correlations: List[Dict[str, Any]]
    logs: List[str]
    ai_analysis: Dict[str, Any]
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


# -------------------------
# RESPONSE
# -------------------------
class AnalyzeResponse(BaseModel):
    summary: str
    findings: List[Finding]
    risk_score: int
    risk_level: str
    insights: List[str]
    ai_analysis: Dict[str, Any]
    anomalies: List[Dict[str, Any]]
    correlations: List[Dict[str, Any]]
    parsed_logs: Optional[List[ParsedLog]] = None
    action: Optional[str] = "allowed"
    masked_output: Optional[str] = None