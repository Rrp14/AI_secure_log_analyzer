def detect_correlations(log_text: str):
    lines = log_text.lower().split("\n")

    events = []
    correlations = []

    for line in lines:
        if "failed login" in line:
            events.append("fail")

        elif "login successful" in line or "logged in" in line:
            events.append("success")

        elif "delete" in line or "rm -rf" in line:
            events.append("delete")

    for i in range(len(events) - 2):
        if events[i:i+3] == ["fail", "fail", "success"]:
            correlations.append({
                "type": "account_compromise",
                "risk": "critical",
                "message": "Brute-force attack led to account compromise"
            })

    for i in range(len(events) - 1):
        if events[i:i+2] == ["success", "delete"]:
            correlations.append({
                "type": "cover_tracks",
                "risk": "critical",
                "message": "Attacker deleting logs to hide activity"
            })

    return correlations