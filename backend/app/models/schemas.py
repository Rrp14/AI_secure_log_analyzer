from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone



class AnalyzeRequest(BaseModel):
    input_type: str
    content: str
    options: Optional[Dict[str, Any]] = None



class Finding(BaseModel):
    type: str
    value: str
    line: int
    risk: str



class ParsedLog(BaseModel):
    line: int
    timestamp: Optional[str]
    level: str
    message: str



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

class LogEntry(BaseModel):
    id: str = Field(..., alias="_id")
    ip: Optional[str] = None
    content: str
    risk_level: Optional[str] = None
    created_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class LogResponse(BaseModel):
    logs: List[LogEntry]
    total: int    