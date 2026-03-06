"""Monitored API definitions and alert configuration."""

import os

# --- Alert notification env vars ---
# Telegram: create bot via @BotFather, get chat ID via @userinfobot
TELEGRAM_BOT_TOKEN_ENV = "TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID_ENV = "TELEGRAM_CHAT_ID"

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
        "key_env": "ALPHAVANTAGE_KEY",
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
        "key_env": "POLYGON_KEY",
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
        "key_env": "FINNHUB_KEY",
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
        "key_env": "TWELVEDATA_KEY",
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
        "key_env": "EODHD_KEY",
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
        "key_env": "FMP_KEY",
        "has_forecasts": False,
        "docs_url": "https://site.financialmodelingprep.com/developer/docs",
        "category": "Fundamentals",
    },
    "fred": {
        "name": "FRED",
        "base_url": "https://api.stlouisfed.org",
        "health": None,
        "endpoints": [
            {"path": "/fred/series/observations", "method": "GET", "params": {"series_id": "DGS10", "limit": "1", "sort_order": "desc", "file_type": "json", "api_key": "{key}"}},
        ],
        "key_env": "FRED_KEY",
        "has_forecasts": False,
        "docs_url": "https://fred.stlouisfed.org/docs/api/fred/",
        "category": "Macro/economic data",
    },
    "coingecko": {
        "name": "CoinGecko",
        "base_url": "https://api.coingecko.com/api/v3",
        "health": None,
        "endpoints": [
            {"path": "/simple/price", "method": "GET", "params": {"ids": "bitcoin", "vs_currencies": "usd"}},
            {"path": "/coins/bitcoin", "method": "GET", "params": {"localization": "false", "tickers": "false", "community_data": "false", "developer_data": "false"}},
        ],
        "has_forecasts": False,
        "docs_url": "https://docs.coingecko.com/",
        "category": "Crypto market data",
    },
    "alpaca": {
        "name": "Alpaca Markets",
        "base_url": "https://data.alpaca.markets",
        "health": None,
        "endpoints": [
            {"path": "/v2/stocks/SPY/trades/latest", "method": "GET", "headers": {"APCA-API-KEY-ID": "{key}", "APCA-API-SECRET-KEY": "{secret}"}},
        ],
        "key_env": "ALPACA_KEY",
        "secret_env": "ALPACA_SECRET",
        "has_forecasts": False,
        "docs_url": "https://docs.alpaca.markets/",
        "category": "Stocks, options, crypto trading + data",
    },
    "yfinance": {
        "name": "Yahoo Finance",
        "base_url": "https://query1.finance.yahoo.com",
        "health": None,
        "endpoints": [
            {"path": "/v8/finance/chart/SPY", "method": "GET", "params": {"range": "1d", "interval": "1d"}, "headers": {"User-Agent": "OathScore/1.0"}},
        ],
        "has_forecasts": False,
        "docs_url": None,
        "category": "Equities, options, fundamentals (unofficial)",
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


def get_api_secret(api_name: str) -> str | None:
    """Get API secret from environment (for APIs needing key+secret)."""
    api = MONITORED_APIS.get(api_name)
    if not api:
        return None
    secret_env = api.get("secret_env")
    if not secret_env:
        return None
    return os.environ.get(secret_env)
