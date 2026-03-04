"""OathScore configuration."""

import os

# API base URL
BASE_URL = os.getenv("OATHSCORE_BASE_URL", "https://api.oathscore.dev")

# Curistat API (for regime/events data)
CURISTAT_API_URL = os.getenv("CURISTAT_API_URL", "https://curistat-api-production.up.railway.app")

# Refresh interval in seconds
NOW_REFRESH_SECONDS = 60

# Exchange calendars to track
EXCHANGES = {
    "CME": {"calendar": "CME", "name": "CME/Globex", "timezone": "America/Chicago"},
    "NYSE": {"calendar": "NYSE", "name": "New York Stock Exchange", "timezone": "America/New_York"},
    "NASDAQ": {"calendar": "NASDAQ", "name": "NASDAQ", "timezone": "America/New_York"},
    "LSE": {"calendar": "LSE", "name": "London Stock Exchange", "timezone": "Europe/London"},
    "EUREX": {"calendar": "XETR", "name": "EUREX", "timezone": "Europe/Berlin"},
    "TSE": {"calendar": "JPX", "name": "Tokyo Stock Exchange", "timezone": "Asia/Tokyo"},
    "HKEX": {"calendar": "HKEX", "name": "Hong Kong Exchange", "timezone": "Asia/Hong_Kong"},
}

# Yahoo Finance symbols for volatility data
VOLATILITY_SYMBOLS = {
    "vix": "^VIX",
    "vix9d": "^VIX9D",
    "vix3m": "^VIX3M",
    "vvix": "^VVIX",
    "skew": "^SKEW",
}

# VIX historical data for percentile calculation (updated periodically)
VIX_PERCENTILE_LOOKBACK_DAYS = 252  # 1 trading year
