"""Rate limiter with tiered API key support."""

import time
from collections import defaultdict

_requests: dict[str, list[float]] = defaultdict(list)

# Tier limits: (now_daily, score_daily)
TIER_LIMITS = {
    "free": (10, 5),
    "founding": (5000, 2500),
    "pro": (10000, 5000),
    "enterprise": (100000, 50000),
}

# Active API keys -> tier mapping (loaded from env/db at startup)
_api_keys: dict[str, str] = {}


def register_key(api_key: str, tier: str):
    """Register an API key with a tier."""
    _api_keys[api_key] = tier


def get_tier(api_key: str | None) -> str:
    """Get tier for an API key. No key = free."""
    if not api_key:
        return "free"
    return _api_keys.get(api_key, "free")


def check_rate_limit(ip: str, endpoint: str, api_key: str | None = None) -> tuple[bool, int]:
    """Check if request is within rate limits. Returns (allowed, remaining)."""
    now = time.time()
    day_start = now - 86400

    tier = get_tier(api_key)
    now_limit, score_limit = TIER_LIMITS[tier]

    # Key-based users tracked by key, free users by IP
    identity = api_key if api_key and tier != "free" else ip
    key = f"{identity}:{endpoint}"

    _requests[key] = [t for t in _requests[key] if t > day_start]

    limit = now_limit if endpoint == "now" else score_limit
    remaining = max(0, limit - len(_requests[key]))

    if remaining <= 0:
        return False, 0

    _requests[key].append(now)
    return True, remaining - 1
