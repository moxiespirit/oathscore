"""Economic event calendar and countdown."""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from src.config import CURISTAT_API_URL

logger = logging.getLogger(__name__)

# Known fixed schedule events (approximate, updated annually)
# These are fallbacks if no live calendar is available
FIXED_EVENTS_2026 = {
    "FOMC": [
        "2026-01-28", "2026-03-18", "2026-05-06", "2026-06-17",
        "2026-07-29", "2026-09-16", "2026-11-04", "2026-12-16",
    ],
    "CPI": [
        "2026-01-14", "2026-02-12", "2026-03-11", "2026-04-10",
        "2026-05-13", "2026-06-10", "2026-07-15", "2026-08-12",
        "2026-09-11", "2026-10-14", "2026-11-12", "2026-12-10",
    ],
}


def _days_until_next(event_dates: list[str], today: str) -> int | None:
    """Days until next occurrence of an event."""
    for d in event_dates:
        if d >= today:
            dt_event = datetime.strptime(d, "%Y-%m-%d")
            dt_today = datetime.strptime(today, "%Y-%m-%d")
            return (dt_event - dt_today).days
    return None


async def get_events_data(now_utc: datetime | None = None) -> dict:
    """Get economic event context."""
    if now_utc is None:
        now_utc = datetime.now(ZoneInfo("UTC"))

    now_et = now_utc.astimezone(ZoneInfo("America/New_York"))
    today_str = now_et.strftime("%Y-%m-%d")

    # Try to get live calendar from Curistat
    next_event = None
    today_remaining = 0
    week_high_impact = 0

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{CURISTAT_API_URL}/api/v1/calendar/week",
                timeout=5.0,
            )
            if resp.status_code == 200:
                cal_data = resp.json()
                events = cal_data if isinstance(cal_data, list) else cal_data.get("events", [])

                for evt in events:
                    evt_time = evt.get("datetime") or evt.get("time")
                    impact = evt.get("impact", "").lower()
                    if impact in ("high", "critical"):
                        week_high_impact += 1

                    evt_date = evt.get("date", "")
                    if evt_date == today_str:
                        today_remaining += 1

                    # Find next upcoming event
                    if evt_time and next_event is None:
                        try:
                            if "T" in str(evt_time):
                                evt_dt = datetime.fromisoformat(str(evt_time).replace("Z", "+00:00"))
                                if evt_dt.tzinfo is None:
                                    evt_dt = evt_dt.replace(tzinfo=ZoneInfo("UTC"))
                                if evt_dt > now_utc:
                                    minutes_until = int((evt_dt - now_utc).total_seconds() / 60)
                                    next_event = {
                                        "name": evt.get("event", evt.get("name", "Unknown")),
                                        "time": evt_dt.isoformat(),
                                        "minutes_until": minutes_until,
                                        "impact": impact or "unknown",
                                    }
                        except (ValueError, TypeError):
                            pass
    except Exception as e:
        logger.warning("Failed to fetch Curistat calendar: %s", e)

    # Compute FOMC and CPI countdowns from fixed schedule
    fomc_days = _days_until_next(FIXED_EVENTS_2026.get("FOMC", []), today_str)
    cpi_days = _days_until_next(FIXED_EVENTS_2026.get("CPI", []), today_str)

    return {
        "next": next_event,
        "today_remaining": today_remaining,
        "week_high_impact": week_high_impact,
        "fomc_days_until": fomc_days,
        "cpi_days_until": cpi_days,
    }
