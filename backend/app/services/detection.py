import re

def detect_sensitive_data(text: str, start_line=1):
    findings = []
    # Split text into individual lines to track line numbers accurately
    lines = text.split("\n")

    # Ensure start_line is at least 1
    start_line = max(1, start_line)

    # Patterns updated to capture the FULL string (removed nested groups)
    # This ensures the Policy Engine can find the exact 'value' to replace.
    patterns = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        # capture only the credential value (handles optional quotes)
        "password": r"password\s*=\s*['\"]?([^'\"\s]+)['\"]?",
        "api_key": r"sk-[A-Za-z0-9]{20,}",
        "aws_secret": r"AKIA[0-9A-Z]{16}",
        "slack_webhook": r"https://hooks\.slack\.com/services/T[A-Z0-9]+/[A-Z0-9]+/[A-Za-z0-9]+",
        "private_key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
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

    for i, line in enumerate(lines):
        # Calculate the absolute line number in the original file
        actual_line = start_line + i

        for key, pattern in patterns.items():
            # Using finditer to catch multiple secrets on the same line
            for match in re.finditer(pattern, line, flags=re.IGNORECASE):
                # If the regex uses a capture group (like password), take the group value.
                # Otherwise fall back to the full match.
                if match.lastindex:
                    value = match.group(1)
                else:
                    value = match.group(0)

                findings.append({
                    "type": key,
                    "value": value.strip(),
                    "line": actual_line,
                    "risk": risk_map.get(key, "medium")
                })

    return findings
