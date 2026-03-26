
RISK_WEIGHTS = {
    "finding": {"critical": 100, "high": 40, "medium": 10, "low": 1},
    "anomaly": {"critical": 100, "high": 50, "medium": 20, "low": 5},
    "correlation": {"critical": 100, "high": 60, "medium": 30, "low": 10},
}

def calculate_risk(findings, anomalies=None, correlations=None):
    """
    Calculates a risk score. A single critical finding will always result in a critical risk level.
    """
    score = 0
    anomalies = anomalies or []
    correlations = correlations or []
    
    has_critical_finding = False
    has_high_finding = False

    # Calculate base score from all items
    for item_list, item_type in [(findings, "finding"), (anomalies, "anomaly"), (correlations, "correlation")]:
        for item in item_list:
            risk = item.get("risk", "low")
            score += RISK_WEIGHTS[item_type].get(risk, 1)
            if risk == "critical":
                has_critical_finding = True
            elif risk == "high":
                has_high_finding = True

 
    if has_critical_finding:
        level = "critical"
    elif has_high_finding and score < 80: # A high finding should at least be HIGH
        level = "high"
    elif score >= 80:
        level = "critical"
    elif score >= 40:
        level = "high"
    elif score >= 10:
        level = "medium"
    else:
        level = "low"

    return int(score), level