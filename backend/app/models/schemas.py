from pydantic import BaseModel
from typing import Any, Dict, List, Literal, Optional

class AnalyzeRequest(BaseModel):
    input_type: str
    content: str
    options: Optional[dict] = {}

class Finding(BaseModel):
    type: str
    value: str
    line: int
    risk: str


class ParsedLog(BaseModel):
    line: int
    timestamp: str | None
    level: str
    message: str


class AnalyzeResponse(BaseModel):
    summary: str
    findings: List[Finding]
    risk_score: int
    risk_level: str
    insights: List[str]
    ai_analysis: Dict[str, Any]
    anomalies: List[Dict[str, Any]]
    correlations: List[Dict[str, Any]] 
    parsed_logs: List[ParsedLog] | None = None ,
    action: Literal["allowed", "masked", "blocked"]
    masked_output: Optional[str] = None