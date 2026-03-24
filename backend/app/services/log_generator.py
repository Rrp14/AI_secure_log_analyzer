import random
from datetime import datetime

def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


#NORMAL LOGS
def normal_logs():
    return random.choice([
        f"[{get_time()}] INFO: Service started successfully",
        f"[{get_time()}] INFO: User viewed dashboard",
        f"[{get_time()}] DEBUG: Cache refreshed"
    ])


#AUTH LOGS
def auth_logs():
    return random.choice([
        f"[{get_time()}] WARN: Failed login for user 'admin' from 185.156.174.12",
        f"[{get_time()}] INFO: User 'john' logged in successfully",
        f"[{get_time()}] ERROR: password=admin123"
    ])


#SQL LOGS
def sql_logs():
    return random.choice([
        f"[{get_time()}] INFO: Executed query SELECT * FROM users",
        f"[{get_time()}] ERROR: SQL Injection attempt ' OR 1=1 --",
        f"[{get_time()}] WARN: Slow query detected (2.5s)"
    ])


#ATTACK LOGS
def attack_logs():
    return random.choice([
        f"[{get_time()}] CRITICAL: AWS key exposed AKIA12345678901234",
        f"[{get_time()}] ALERT: Unauthorized SSH access detected",
        f"[{get_time()}] CRITICAL: Exposed Slack webhook https://hooks.slack.com"
    ])


#SYSTEM LOGS
def system_logs():
    return random.choice([
        f"[{get_time()}] INFO: CPU usage 45%",
        f"[{get_time()}] WARN: Memory usage high",
        f"[{get_time()}] DEBUG: Background job completed"
    ])


#MAIN GENERATOR
def generate_log(log_type="mixed"):
    mapping = {
        "normal": normal_logs,
        "auth": auth_logs,
        "sql": sql_logs,
        "attack": attack_logs,
        "system": system_logs
    }

    if log_type == "mixed":
        return random.choice(list(mapping.values()))()

    return mapping.get(log_type, normal_logs)()

def attack_sequence():
    t = get_time()
    return [
        f"[{t}] WARN: Failed login for user 'admin' from 185.156.174.12",
        f"[{t}] WARN: Failed login for user 'admin' from 185.156.174.12",
        f"[{t}] ALERT: User 'admin' logged in from 185.156.174.12",
        f"[{t}] INFO: User executed rm -rf /logs"
    ]