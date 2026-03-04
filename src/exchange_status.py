"""Exchange open/close status derived from exchange_calendars schedules."""

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import exchange_calendars as xcals
import pandas as pd

from src.config import EXCHANGES

logger = logging.getLogger(__name__)

# Cache calendar objects (expensive to create)
_calendar_cache: dict[str, xcals.ExchangeCalendar] = {}


def _get_calendar(cal_name: str) -> xcals.ExchangeCalendar:
    if cal_name not in _calendar_cache:
        _calendar_cache[cal_name] = xcals.get_calendar(cal_name)
    return _calendar_cache[cal_name]


def _format_time(dt: datetime, tz_name: str) -> str:
    tz = ZoneInfo(tz_name)
    local = dt.astimezone(tz)
    abbr = local.strftime("%Z")
    # Windows doesn't support %-I, use %#I or strip manually
    hour = local.strftime("%I").lstrip("0") or "12"
    minute = local.strftime("%M")
    ampm = local.strftime("%p")
    return f"{hour}:{minute} {ampm} {abbr}"


def get_exchange_status(now_utc: datetime | None = None) -> dict:
    """Return open/close status for all tracked exchanges."""
    if now_utc is None:
        now_utc = datetime.now(ZoneInfo("UTC"))

    now_ts = pd.Timestamp(now_utc, tz="UTC")
    result = {}

    for code, info in EXCHANGES.items():
        try:
            cal = _get_calendar(info["calendar"])
        except Exception:
            result[code] = {"status": "unknown", "next": "calendar unavailable", "minutes_until": -1}
            continue
        tz_name = info["timezone"]

        try:
            is_open = cal.is_open_on_minute(now_ts, side="left")
        except Exception:
            is_open = False

        if is_open:
            try:
                session = cal.minute_to_session(now_ts, direction="none")
                close_time = cal.session_close(session)
                close_dt = close_time.to_pydatetime()
                if close_dt.tzinfo is None:
                    close_dt = close_dt.replace(tzinfo=ZoneInfo("UTC"))
                minutes_until = max(0, int((close_dt - now_utc).total_seconds() / 60))
                result[code] = {
                    "status": "open",
                    "next": f"close {_format_time(close_dt, tz_name)}",
                    "minutes_until": minutes_until,
                }
            except Exception as e:
                logger.warning("Error getting close time for %s: %s", code, e)
                result[code] = {"status": "open", "next": "close time unknown", "minutes_until": -1}
        else:
            try:
                # Search next 7 calendar days for next session
                start = now_ts.normalize()
                end = start + pd.Timedelta(days=7)
                # Clamp to calendar bounds
                if end > cal.last_session:
                    end = pd.Timestamp(cal.last_session)
                if start < cal.first_session:
                    start = pd.Timestamp(cal.first_session)

                next_sessions = cal.sessions_in_range(start, end)
                next_open_dt = None
                for sess in next_sessions:
                    open_time = cal.session_open(sess)
                    open_dt = open_time.to_pydatetime()
                    if open_dt.tzinfo is None:
                        open_dt = open_dt.replace(tzinfo=ZoneInfo("UTC"))
                    if open_dt > now_utc:
                        next_open_dt = open_dt
                        break

                if next_open_dt:
                    minutes_until = max(0, int((next_open_dt - now_utc).total_seconds() / 60))
                    result[code] = {
                        "status": "closed",
                        "next": f"open {_format_time(next_open_dt, tz_name)}",
                        "minutes_until": minutes_until,
                    }
                else:
                    result[code] = {"status": "closed", "next": "unknown", "minutes_until": -1}
            except Exception as e:
                logger.warning("Error getting next open for %s: %s", code, e)
                result[code] = {"status": "closed", "next": "unknown", "minutes_until": -1}

    return result
