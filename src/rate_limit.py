"""Simple in-memory rate limiter."""

import time
from collections import defaultdict

_requests: dict[str, list[float]] = defaultdict(list)

DAILY_LIMIT_NOW = 100
DAILY_LIMIT_SCORE = 50


def check_rate_limit(ip: str, endpoint: str) -> tuple[bool, int]:
    """Check if request is within rate limits. Returns (allowed, remaining)."""
    now = time.time()
    day_start = now - 86400
    key = f"{ip}:{endpoint}"

    _requests[key] = [t for t in _requests[key] if t > day_start]

    limit = DAILY_LIMIT_NOW if endpoint == "now" else DAILY_LIMIT_SCORE
    remaining = max(0, limit - len(_requests[key]))

    if remaining <= 0:
        return False, 0

    _requests[key].append(now)
    return True, remaining - 1
