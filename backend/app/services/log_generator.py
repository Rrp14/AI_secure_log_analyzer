import random
from datetime import datetime


def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")



def random_ip():
    return ".".join(str(random.randint(1, 255)) for _ in range(4))


def random_user():
    return random.choice(["admin", "root", "john", "alice", "guest"])


def random_endpoint():
    return random.choice([
        "/login",
        "/dashboard",
        "/api/data",
        "/settings",
        "/admin"
    ])



def normal_log():
    ip = random_ip()
    user = random_user()

    logs = [
        f"INFO: System health check passed | ip={ip}",
        f"INFO: Memory usage normal | ip={ip}",
        f"INFO: CPU usage at {random.randint(20, 70)}% | ip={ip}",
        f"INFO: User {user} accessed dashboard | ip={ip}",
        f"INFO: Scheduled job completed | ip={ip}",
        f"INFO: Connection established to DB | ip={ip}",
        f"INFO: Service running normally | ip={ip}",
        f"INFO: GET {random_endpoint()} | status=200 | ip={ip}"
    ]

    return random.choice(logs)



def suspicious_log():
    ip = random_ip()
    user = random_user()

    logs = [
        f"WARN: Failed login for user '{user}' from {ip}",
        f"WARN: Multiple login attempts detected from {ip}",
        f"WARN: Unexpected input received from API | ip={ip}",
        f"WARN: High memory usage detected | ip={ip}"
    ]

    return random.choice(logs)


def critical_log():
    ip = random_ip()
    user = random_user()

    logs = [
        f"CRITICAL: Unauthorized SSH access detected on port 22 | ip={ip}",
        f"ALERT: User '{user}' logged in from unknown IP {ip}",
        f"ERROR: password=admin123 found in config",
        f"CRITICAL: AWS_SECRET_KEY=AKIAJSIEJS838DFKJD83 exposed",
        f"INFO: User {user} executed: 'rm -rf /var/www/html/logs'",
        f"WARN: Sensitive data leak: base64(S3_SECRET_KEY) = {random.getrandbits(128)}"
    ]

    return random.choice(logs)


def generate_log():
    r = random.random()

    if r < 0.85:
        log = normal_log()
    elif r < 0.95:
        log = suspicious_log()
    else:
        log = critical_log()

    return f"[{get_timestamp()}] {log}"


def attack_sequence():
    ip = random_ip()

    return [
        f"[{get_timestamp()}] INFO: Connection attempt from {ip} on port 22",
        f"[{get_timestamp()}] WARN: Failed login for user 'admin' from {ip}",
        f"[{get_timestamp()}] WARN: Failed login for user 'admin' from {ip}",
        f"[{get_timestamp()}] WARN: Failed login for user 'root' from {ip}",
        f"[{get_timestamp()}] CRITICAL: Unauthorized SSH access detected on port 22 | ip={ip}",
        f"[{get_timestamp()}] ALERT: User 'admin' logged in from {ip}",
        f"[{get_timestamp()}] INFO: User admin executed: 'rm -rf /var/www/html/logs'"
    ]