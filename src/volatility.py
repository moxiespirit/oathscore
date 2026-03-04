"""Fetch volatility data from Yahoo Finance."""

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx

from src.config import VOLATILITY_SYMBOLS

logger = logging.getLogger(__name__)

# Yahoo Finance v8 quote endpoint (no API key needed)
YAHOO_QUOTE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"


async def _fetch_yahoo_quote(client: httpx.AsyncClient, symbol: str) -> float | None:
    """Fetch latest price for a Yahoo Finance symbol."""
    try:
        resp = await client.get(
            YAHOO_QUOTE_URL.format(symbol=symbol),
            params={"interval": "1d", "range": "5d"},
            headers={"User-Agent": "OathScore/1.0"},
            timeout=10.0,
        )
        if resp.status_code != 200:
            logger.warning("Yahoo returned %d for %s", resp.status_code, symbol)
            return None

        data = resp.json()
        result = data.get("chart", {}).get("result", [])
        if not result:
            return None

        meta = result[0].get("meta", {})
        price = meta.get("regularMarketPrice")
        if price is None:
            price = meta.get("previousClose")
        return float(price) if price is not None else None

    except Exception as e:
        logger.warning("Yahoo fetch failed for %s: %s", symbol, e)
        return None


async def get_volatility_data() -> dict:
    """Fetch all volatility readings."""
    result = {}
    async with httpx.AsyncClient() as client:
        for key, symbol in VOLATILITY_SYMBOLS.items():
            value = await _fetch_yahoo_quote(client, symbol)
            result[key] = round(value, 2) if value is not None else None

    # Compute derived fields
    vix = result.get("vix")
    vix3m = result.get("vix3m")

    if vix is not None and vix3m is not None:
        if vix < vix3m:
            result["term_structure"] = "contango"
        elif vix > vix3m:
            result["term_structure"] = "backwardation"
        else:
            result["term_structure"] = "flat"
    else:
        result["term_structure"] = None

    return result
