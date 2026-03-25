from app.services.detection import detect_sensitive_data

def test_detect_password_and_email():
    text = "email=admin@company.com\npassword=admin123\napi_key=sk-ABCDEFGHIJKLMNOPQRSTUV"
    findings = detect_sensitive_data(text)

    types = {f["type"] for f in findings}
    assert "email" in types
    assert "password" in types
    assert "api_key" in types

    # Check password value is only the secret 
    pw = next(f for f in findings if f["type"] == "password")
    assert pw["value"] == "admin123"
    assert pw["line"] == 2

def test_detect_ip_and_aws_secret():
    text = "Client 185.156.174.12 used AWS key AKIAJSIEJS838DFKJD83"
    findings = detect_sensitive_data(text)

    types = {f["type"] for f in findings}
    assert "ip_address" in types
    assert "aws_secret" in types
