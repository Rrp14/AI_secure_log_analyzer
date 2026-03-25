from app.main import app  # keeps import (not strictly needed but fine)

def test_analyze_text_password_masking(test_client):
    resp = test_client.post(
        "/analyze",
        data={
            "input_type": "text",
            "content": "user=admin password=admin123",
            "options": '{"mask": true, "include_masked": true}'
        }
    )
    assert resp.status_code == 200
    data = resp.json()

    pw_findings = [f for f in data["findings"] if f["type"] == "password"]
    assert len(pw_findings) == 1
    assert pw_findings[0]["risk"] in ("critical", "high", "medium")

    assert any("sensitive" in s.lower() or "critical" in s.lower() for s in data["insights"])


def test_analyze_invalid_input(test_client):
    resp = test_client.post(
        "/analyze",
        data={"input_type": "text"}
    )
    assert resp.status_code in (400, 422)
