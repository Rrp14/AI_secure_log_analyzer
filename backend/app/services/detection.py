import re

def detect_sensitive_data(text: str, start_line=1):
    findings = []
    lines = text.split("\n")

    patterns = {
        "email": r"\S+@\S+",
        "password": r"password\s*=\s*\S+",
        "api_key": r"sk-[A-Za-z0-9]+",
        "aws_secret": r"AKIA[0-9A-Z]{16}",
        "slack_webhook": r"https://hooks\.slack\.com\S*",
        "private_key": r"-----BEGIN.*PRIVATE KEY-----",
        "ip_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    }

    risk_map = {
        "email": "low",
        "ip_address": "low",
        "password": "critical",
        "private_key": "critical",
        "api_key": "high",
        "aws_secret": "high",
        "slack_webhook": "high"
    }

    for i, line in enumerate(lines, start=start_line):
        for key, pattern in patterns.items():
            matches = re.findall(pattern, line)
            for match in matches:
                findings.append({
                    "type": key,
                    "value": match,
                    "line": i,
                    "risk": risk_map[key]
                })

    return findings