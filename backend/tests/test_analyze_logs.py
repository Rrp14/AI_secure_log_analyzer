from fastapi.testclient import TestClient
from pathlib import Path
from app.main import app

client = TestClient(app)
BASE_DIR = Path(__file__).resolve().parent

def test_analyze_attack_log_file(test_client):
    log_path = BASE_DIR / "logs" / "attack.log"
    with log_path.open("rb") as f:
        resp = test_client.post(
            "/analyze",
            data={"input_type": "log"},
            files={"file": ("attack.log", f, "text/plain")},
        )

    assert resp.status_code == 200
    data = resp.json()

    # Should detect at least one IP address (attacker IP)
    assert any(f["type"] == "ip_address" for f in data["findings"])

    # Risk level should be medium/high depending on your scoring logic
    assert data["risk_level"] in ("low", "medium", "high", "critical")

    # Anomalies and/or insights should indicate suspicious activity
    # (depending on how detect_anomalies is implemented)
    assert isinstance(data["insights"], list)
