def mask_sensitive_data(text: str, findings: list):
    lines = text.split("\n")
    SKIP_MASKING = ["ip_address", "timestamp", "user_id"]

    for f in findings:
        if f.get("type") in SKIP_MASKING:
            continue

        line_idx = f.get("line", 1) - 1
        value = f.get("value")

        if value and 0 <= line_idx < len(lines):
            if len(value) > 4:
                masked = value[:2] + "*" * (len(value) - 4) + value[-2:]
            else:
                masked = "*" * len(value)
            
            # Update the specific line
            lines[line_idx] = lines[line_idx].replace(value, masked)

    return "\n".join(lines)

def apply_policy(text: str, findings: list, anomalies: list, correlations: list, risk_level: str, options: dict):
    """
    Determines the appropriate action and performs masking.
    """
    action = "allowed"  # Default action

    # --- Rule-Based Policy Decisions ---
    if risk_level == "critical":
        action = "block"
    elif risk_level == "high":
        action = "monitor"

    if any(c.get("type") == "account_compromise" for c in correlations):
        action = "force_password_reset"
    if any(a.get("type") == "brute_force_ip" for a in anomalies):
        action = "block_ip"
    
    masked_output = text
    if options.get("mask", False) and findings:
        masked_output = mask_sensitive_data(text, findings)

    return {
        "action": action,
        "masked_text": masked_output
    }
