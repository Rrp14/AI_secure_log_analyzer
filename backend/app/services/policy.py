def mask_sensitive_data(text: str, findings: list):
    lines = text.split("\n")
    
    # Define what is OK to show (Whitelisting)
    SKIP_MASKING = ["ip_address", "timestamp", "user_id"]

    for f in findings:
        # Skip masking if the type is in our 'Forensic Important' list
        if f.get("type") in SKIP_MASKING:
            continue

        line_idx = f["line"] - 1
        value = f.get("value")

        if value and 0 <= line_idx < len(lines):
            # Masking logic
            if len(value) > 4:
                masked = value[:2] + "*" * (len(value) - 4) + value[-2:]
            else:
                masked = "*" * len(value)

            lines[line_idx] = lines[line_idx].replace(value, masked)

    return "\n".join(lines)



def apply_policy(text: str, findings: list, risk_level: str, options: dict):
    should_mask = options.get("mask", True)
    should_block = options.get("block_high_risk", False)

    # 1. Start with the original text
    final_text = text
    action = "allowed"

    # 2. Try masking
    if should_mask and findings:
        masked_version = mask_sensitive_data(text, findings)
        
        # Only set action to 'masked' if something actually changed!
        if masked_version != text:
            final_text = masked_version
            action = "masked"

    # 3. Block overrides (High priority)
    if should_block and risk_level in ["high", "critical"]:
        final_text = "[BLOCKED: Sensitive content removed]"
        action = "blocked"

    return {
        "masked_text": final_text,
        "action": action
    }
