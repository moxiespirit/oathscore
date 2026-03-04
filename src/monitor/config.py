"""Monitored API definitions."""

import os

# Each API we monitor: name, base_url, health endpoint, sample endpoints
MONITORED_APIS = {
    "curistat": {
        "name": "Curistat",
        "base_url": "https://curistat-api-production.up.railway.app",
        "health": "/health",
        "endpoints": [
            {"path": "/api/v1/forecast/es", "method": "GET"},
            {"path": "/api/v1/calendar/week", "method": "GET"},
        ],
        "has_forecasts": True,
        "docs_url": "https://curistat.com",
        "category": "Futures volatility forecasting",
    },
    "alphavantage": {
        "name": "Alpha Vantage",
        "base_url": "https://www.alphavantage.co",
        "health": None,
        "endpoints": [
            {"path": "/query", "method": "GET", "params": {"function": "TIME_SERIES_DAILY", "symbol": "SPY", "apikey": "{key}"}},
        ],
        "key_env": "ALPHAVANTAGE_API_KEY",
        "has_forecasts": False,
        "docs_url": "https://www.alphavantage.co/documentation/",
        "category": "Equities, macro, forex",
    },
    "polygon": {
        "name": "Polygon.io",
        "base_url": "https://api.polygon.io",
        "health": None,
        "endpoints": [
            {"path": "/v2/aggs/ticker/SPY/prev", "method": "GET", "params": {"apiKey": "{key}"}},
        ],
        "key_env": "POLYGON_API_KEY",
        "has_forecasts": False,
        "docs_url": "https://polygon.io/docs",
        "category": "Market data, status",
    },
    "finnhub": {
        "name": "Finnhub",
        "base_url": "https://finnhub.io/api/v1",
        "health": None,
        "endpoints": [
            {"path": "/quote", "method": "GET", "params": {"symbol": "SPY", "token": "{key}"}},
            {"path": "/calendar/economic", "method": "GET", "params": {"token": "{key}"}},
        ],
        "key_env": "FINNHUB_API_KEY",
        "has_forecasts": False,
        "docs_url": "https://finnhub.io/docs/api",
        "category": "Multi-asset, calendar",
    },
    "twelvedata": {
        "name": "Twelve Data",
        "base_url": "https://api.twelvedata.com",
        "health": None,
        "endpoints": [
            {"path": "/time_series", "method": "GET", "params": {"symbol": "SPY", "interval": "1day", "outputsize": "1", "apikey": "{key}"}},
        ],
        "key_env": "TWELVEDATA_API_KEY",
        "has_forecasts": False,
        "docs_url": "https://twelvedata.com/docs",
        "category": "Market data",
    },
    "eodhd": {
        "name": "EODHD",
        "base_url": "https://eodhd.com/api",
        "health": None,
        "endpoints": [
            {"path": "/real-time/SPY.US", "method": "GET", "params": {"api_token": "{key}", "fmt": "json"}},
        ],
        "key_env": "EODHD_API_KEY",
        "has_forecasts": False,
        "docs_url": "https://eodhd.com/financial-apis/",
        "category": "Historical data",
    },
    "fmp": {
        "name": "Financial Modeling Prep",
        "base_url": "https://financialmodelingprep.com/api/v3",
        "health": None,
        "endpoints": [
            {"path": "/quote/SPY", "method": "GET", "params": {"apikey": "{key}"}},
        ],
        "key_env": "FMP_API_KEY",
        "has_forecasts": False,
        "docs_url": "https://site.financialmodelingprep.com/developer/docs",
        "category": "Fundamentals",
    },
}


def get_api_key(api_name: str) -> str | None:
    """Get API key from environment."""
    api = MONITORED_APIS.get(api_name)
    if not api:
        return None
    key_env = api.get("key_env")
    if not key_env:
        return None  # No key needed (e.g., Curistat)
    return os.environ.get(key_env)
