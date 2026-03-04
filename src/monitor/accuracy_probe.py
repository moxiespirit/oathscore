"""Accuracy probe — snapshots forecasts and compares to actuals next day."""

import logging
from datetime import datetime, timezone, timedelta

import httpx

from src.monitor.store import _load, _save

logger = logging.getLogger(__name__)

# APIs that make verifiable claims (forecasts, predictions, ratings)
FORECAST_ENDPOINTS = {
    "curistat": {
        "forecast_url": "https://curistat-api-production.up.railway.app/api/v1/forecast/es",
        "actual_url": None,  # We verify against Yahoo Finance ES actual vol
        "extract_forecast": lambda d: d.get("forecast", {}).get("predicted_range_points") if isinstance(d, dict) else None,
        "extract_date": lambda d: d.get("forecast", {}).get("date") if isinstance(d, dict) else None,
    },
}

# Yahoo Finance for actuals
ACTUAL_SOURCES = {
    "es_range": {
        "url": "https://query1.finance.yahoo.com/v8/finance/chart/ES=F",
        "params": {"interval": "1d", "range": "5d"},
        "extract": lambda d: _extract_es_range(d),
    },
}


def _extract_es_range(data: dict) -> dict | None:
    """Extract daily high-low range from ES futures Yahoo data."""
    try:
        result = data["chart"]["result"][0]
        timestamps = result["timestamp"]
        highs = result["indicators"]["quote"][0]["high"]
        lows = result["indicators"]["quote"][0]["low"]
        ranges = {}
        for i, ts in enumerate(timestamps):
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            date_str = dt.strftime("%Y-%m-%d")
            if highs[i] is not None and lows[i] is not None:
                ranges[date_str] = round(highs[i] - lows[i], 2)
        return ranges
    except (KeyError, IndexError, TypeError):
        return None


async def snapshot_forecasts() -> list[dict]:
    """Take a snapshot of current forecasts for later verification."""
    results = []
    async with httpx.AsyncClient(timeout=15.0) as client:
        for api_name, config in FORECAST_ENDPOINTS.items():
            try:
                resp = await client.get(config["forecast_url"])
                if resp.status_code != 200:
                    continue
                data = resp.json()
                forecast_val = config["extract_forecast"](data)
                forecast_date = config["extract_date"](data)

                if forecast_val is not None:
                    snapshot = {
                        "api_name": api_name,
                        "forecast_date": forecast_date,
                        "forecast_value": forecast_val,
                        "actual_value": None,
                        "accuracy_score": None,
                        "snapshot_time": datetime.now(timezone.utc).isoformat(),
                    }
                    snapshots = _load("forecast_snapshots.json")
                    snapshots.append(snapshot)
                    _save("forecast_snapshots.json", snapshots)
                    results.append(snapshot)
                    logger.info("Snapshot %s forecast for %s: %s", api_name, forecast_date, forecast_val)
            except Exception as e:
                logger.warning("Forecast snapshot failed for %s: %s", api_name, e)

    return results


async def verify_forecasts() -> list[dict]:
    """Compare yesterday's forecast snapshots against actual values."""
    results = []
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

    # Get actual ES range from Yahoo
    actual_ranges = None
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            src = ACTUAL_SOURCES["es_range"]
            resp = await client.get(src["url"], params=src["params"])
            if resp.status_code == 200:
                actual_ranges = src["extract"](resp.json())
        except Exception as e:
            logger.warning("Failed to fetch ES actuals: %s", e)

    if not actual_ranges:
        return results

    # Find unverified snapshots for yesterday
    snapshots = _load("forecast_snapshots.json")
    updated = False
    for snap in snapshots:
        if snap.get("forecast_date") == yesterday and snap.get("actual_value") is None:
            actual = actual_ranges.get(yesterday)
            if actual is not None:
                snap["actual_value"] = actual
                forecast = snap.get("forecast_value")
                if isinstance(forecast, (int, float)) and isinstance(actual, (int, float)) and actual > 0:
                    error_pct = abs(forecast - actual) / actual * 100
                    # Score: 100 if exact, 0 if >50% off
                    snap["accuracy_score"] = round(max(0, 100 - error_pct * 2), 1)
                updated = True
                results.append(snap)
                logger.info("Verified %s: forecast=%s, actual=%s, score=%s",
                           snap["api_name"], forecast, actual, snap.get("accuracy_score"))

    if updated:
        _save("forecast_snapshots.json", snapshots)

    return results
