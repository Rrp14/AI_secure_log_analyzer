from pydantic import BaseModel
from typing import Any, Dict, List, Optional

class AnalyzeRequest(BaseModel):
    input_type: str
    content: str
    options: Optional[dict] = {}

class Finding(BaseModel):
    type: str
    value: str
    line: int
    risk: str


class AnalyzeResponse(BaseModel):
    summary: str
    findings: List[Finding]
    risk_score: int
    risk_level: str
    insights: List[str]
    ai_analysis: Dict[str, Any]  