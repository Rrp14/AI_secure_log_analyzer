import re

def detect_anomalies(log_text: str):
    lines = log_text.lower().split("\n")

    ip_failures = {}
    anomalies = []

    for line in lines:
        if "failed" in line and ("login" in line or "password" in line):

            ip_match = re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", line)
            ip = ip_match.group(0) if ip_match else "unknown"

            ip_failures[ip] = ip_failures.get(ip, 0) + 1

            if ip_failures[ip] == 3:
                anomalies.append({
                    "type": "brute_force_ip",
                    "ip": ip,
                    "count": ip_failures[ip],
                    "risk": "high",
                    "message": f"Brute-force attack detected from IP {ip}"
                })
            if "unauthorized ssh access" in line:
                anomalies.append({
        "type": "unauthorized_access",
        "risk": "critical",
        "message": "Unauthorized SSH access detected"
    })    

    return anomalies