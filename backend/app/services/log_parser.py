import re

LOG_PATTERN = re.compile(
    r"\[(?P<timestamp>.*?)\]\s+(?P<level>[A-Z]+):\s+(?P<message>.*)"
)


def parse_logs(lines):
    parsed_logs = []

    for i, line in enumerate(lines, start=1):
        match = LOG_PATTERN.match(line)

        if match:
            parsed_logs.append({
                "line": i,
                "timestamp": match.group("timestamp"),
                "level": match.group("level"),
                "message": match.group("message")
            })
        else:
            parsed_logs.append({
                "line": i,
                "timestamp": None,
                "level": "UNKNOWN",
                "message": line
            })

    return parsed_logs