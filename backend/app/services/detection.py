import re

def detect_sensitive_data(text: str):
    findings = []
    lines = text.split("\n")

    email_pattern = r"\S+@\S+"
    password_pattern = r"password\s*=\s*\S+"
    api_key_pattern = r"sk-[A-Za-z0-9]+"

    for i, line in enumerate(lines, start=1):

        # Email
        emails = re.findall(email_pattern, line)
        for e in emails:
            findings.append({
                "type": "email",
                "value": e,
                "line": i,
                "risk": "low"
            })

        # Password
        passwords = re.findall(password_pattern, line)
        for p in passwords:
            findings.append({
                "type": "password",
                "value": p,
                "line": i,
                "risk": "critical"
            })

        # API Key
        keys = re.findall(api_key_pattern, line)
        for k in keys:
            findings.append({
                "type": "api_key",
                "value": k,
                "line": i,
                "risk": "high"
            })

    return findings