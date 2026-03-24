def calculate_risk(findings, anomalies=None, correlations=None):
    score = 0

    for f in findings:
        if f["risk"] == "critical":
            score += 5
        elif f["risk"] == "high":
            score += 3
        elif f["risk"] == "medium":
            score += 2
        else:
            score += 1

    if anomalies:
        for a in anomalies:
            if a["risk"] == "high":
                score += 4

    if correlations:
        for c in correlations:
            if c["risk"] == "critical":
                score += 6

    #PRIORITY RULE
    if any(f["risk"] == "critical" for f in findings):
        return score, "critical"

    # Normal thresholds
    if score >= 12:
        level = "critical"
    elif score >= 8:
        level = "high"
    elif score >= 4:
        level = "medium"
    else:
        level = "low"

    return score, level