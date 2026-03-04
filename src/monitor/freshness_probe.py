"""Data freshness probe — measures how stale API data actually is."""

import logging
from datetime import datetime, timezone

import httpx

from src.monitor.config import MONITORED_APIS, get_api_key
from src.monitor.store import store_freshness

logger = logging.getLogger(__name__)


def _extract_timestamp(data, api_name: str) -> datetime | None:
    """Try to find a timestamp in the API response to measure freshness."""
    if isinstance(data, dict):
        # Common timestamp field names
        for key in ("timestamp", "updated_at", "last_updated", "date", "datetime", "time", "lastUpdated"):
            if key in data:
                val = data[key]
                if isinstance(val, str):
                    try:
                        dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        return dt
                    except (ValueError, TypeError):
                        pass
                elif isinstance(val, (int, float)) and val > 1e9:
                    return datetime.fromtimestamp(val, tz=timezone.utc)

        # Check nested: Meta-Data, meta, etc.
        for key in ("Meta Data", "meta", "metadata"):
            if key in data and isinstance(data[key], dict):
                result = _extract_timestamp(data[key], api_name)
                if result:
                    return result

    return None


async def check_freshness() -> list[dict]:
    """Check data freshness for all monitored APIs."""
    results = []
    now = datetime.now(timezone.utc)

    async with httpx.AsyncClient(timeout=15.0) as client:
        for api_name, api in MONITORED_APIS.items():
            for ep in api.get("endpoints", []):
                params = dict(ep.get("params", {}))
                key = get_api_key(api_name)
                if key:
                    params = {k: (key if v == "{key}" else v) for k, v in params.items()}
                elif any(v == "{key}" for v in params.values()):
                    continue

                url = f"{api['base_url']}{ep['path']}"
                try:
                    resp = await client.get(url, params=params)
                    if resp.status_code != 200:
                        continue

                    data = resp.json()
                    data_ts = _extract_timestamp(data, api_name)

                    if data_ts:
                        age_seconds = int((now - data_ts).total_seconds())
                    else:
                        age_seconds = None

                    result = {
                        "api_name": api_name,
                        "endpoint": ep["path"],
                        "data_timestamp": data_ts.isoformat() if data_ts else None,
                        "age_seconds": age_seconds,
                        "timestamp": now.isoformat(),
                    }
                    results.append(result)
                    await store_freshness(result)

                    if age_seconds is not None:
                        logger.info("Freshness %s%s: %ds old", api_name, ep["path"], age_seconds)
                    else:
                        logger.info("Freshness %s%s: no timestamp found", api_name, ep["path"])

                except Exception as e:
                    logger.warning("Freshness check failed for %s %s: %s", api_name, ep["path"], e)

    return results
