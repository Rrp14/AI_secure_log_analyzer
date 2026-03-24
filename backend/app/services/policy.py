def mask_sensitive_data(text: str, findings: list):
    lines = text.split("\n")
    SKIP_MASKING = ["ip_address", "timestamp", "user_id"]

    for f in findings:
        if f.get("type") in SKIP_MASKING:
            continue

        # Use .get("line", 1) to avoid 0 or None issues
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

def apply_policy(text: str, findings: list, risk_level: str, options: dict):
    # Ensure keys match your Postman input (lowercase 'mask')
    should_mask = options.get("mask", False) 
    
    response = {
        "masked_text": text,
        "action": "allowed"
    }

    if should_mask and findings:
        response["masked_text"] = mask_sensitive_data(text, findings)
        # Verify if text actually changed
        if response["masked_text"] != text:
            response["action"] = "masked"

    return response
