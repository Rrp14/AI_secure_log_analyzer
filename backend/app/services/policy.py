def mask_sensitive_data(text: str, findings: list):
    lines = text.split("\n")

    for f in findings:
        line_idx = f["line"] - 1
        value = f.get("value")

        if value and 0 <= line_idx < len(lines):
            if len(value) > 4:
                masked = value[:2] + "*" * (len(value) - 4) + value[-2:]
            else:
                masked = "*" * len(value)

            lines[line_idx] = lines[line_idx].replace(value, masked)

    return "\n".join(lines)


def apply_policy(text: str, findings: list, risk_level: str, options: dict):

    # Safe defaults
    should_mask = options.get("mask", True)
    should_block = options.get("block_high_risk", False)

    response = {
        "masked_text": text,
        "action": "allowed"
    }

    # Mask only if findings exist
    if should_mask and findings:
        response["masked_text"] = mask_sensitive_data(text, findings)
        response["action"] = "masked"

    # Block overrides everything
    if should_block and risk_level in ["high", "critical"]:
        response["masked_text"] = "[BLOCKED: Sensitive content removed]"
        response["action"] = "blocked"

    return response