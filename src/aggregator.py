"""Main aggregator: assembles the /now response from all data sources."""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from src.exchange_status import get_exchange_status
from src.volatility import get_volatility_data
from src.events import get_events_data

logger = logging.getLogger(__name__)


async def build_now_response() -> dict:
    """Build the complete /now response."""
    now_utc = datetime.now(ZoneInfo("UTC"))

    # Gather all data (exchange status is sync, others are async)
    exchanges = get_exchange_status(now_utc)
    volatility = await get_volatility_data()
    events = await get_events_data(now_utc)

    # Data health: track which sources returned data
    degraded = []
    if volatility.get("vix") is None:
        degraded.append({"source": "yahoo_vix", "reason": "fetch failed"})
    if volatility.get("vvix") is None:
        degraded.append({"source": "yahoo_vvix", "reason": "fetch failed"})

    return {
        "timestamp": now_utc.isoformat(),
        "exchanges": exchanges,
        "volatility": {
            "vix": volatility.get("vix"),
            "vix9d": volatility.get("vix9d"),
            "vix3m": volatility.get("vix3m"),
            "vvix": volatility.get("vvix"),
            "skew": volatility.get("skew"),
            "term_structure": volatility.get("term_structure"),
        },
        "events": events,
        "data_health": {
            "all_fresh": len(degraded) == 0,
            "degraded": degraded,
        },
        "meta": {
            "version": "1.0.0",
            "source": "oathscore.dev",
            "refresh_interval_seconds": 60,
        },
    }
