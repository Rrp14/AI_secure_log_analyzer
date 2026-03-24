from kafka import KafkaConsumer
import json

from app.services.detection import detect_sensitive_data
from app.services.risk import calculate_risk
from app.services.policy import apply_policy
from app.services.anomaly import detect_anomalies
from app.services.correlation import detect_correlations

TOPIC = "logs_topic"

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers="127.0.0.1:9092",
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    group_id="log-group"
)


def start_consumer():
    print("Kafka Consumer started...")

    options_dict = {
        "mask": True,
        "block_high_risk": True,
        "include_parsed": True,
        "include_masked": True
    }

    for message in consumer:
        try:
            log_data = message.value
            log = log_data["log"]

            print("\nReceived:", log)

            findings = detect_sensitive_data(log)

            parsed_logs = [{
                "line": 1,
                "timestamp": None,
                "level": "UNKNOWN",
                "message": log
            }]

            anomalies = detect_anomalies(log)
            correlations = detect_correlations(log)

            risk_score, risk_level = calculate_risk(
                findings,
                anomalies,
                correlations
            )

            policy_result = apply_policy(
                log,
                findings,
                risk_level,
                options_dict
            )

            #Summary
            if findings:
                summary = f"{len(findings)} sensitive findings detected. Risk level: {risk_level.upper()}"
            else:
                summary = "No sensitive data detected"

            #Insights
            insights = []

            if anomalies:
                insights.append("Suspicious activity detected")

            if correlations:
                insights.append("Multi-stage attack detected")

            if any(f["risk"] in ["high", "critical"] for f in findings):
                insights.append("Sensitive data exposure detected")

            if not insights:
                insights.append("No major risks detected")

            result = {
                "summary": summary,
                "findings": findings,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "insights": insights,
                "ai_analysis": {},  # skipped in real-time for performance
                "anomalies": anomalies,
                "correlations": correlations,
                "parsed_logs": parsed_logs if options_dict.get("include_parsed") else [],
                "action": policy_result["action"],
                "masked_output": policy_result["masked_text"] if options_dict.get("include_masked") else None
            }

            print("\n📊 FINAL RESULT:")
            print(result)

        except Exception as e:
            print("Consumer error:", e)


if __name__ == "__main__":
    start_consumer()