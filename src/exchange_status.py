"""Exchange open/close status derived from exchange_calendars schedules."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import exchange_calendars as xcals
import pandas as pd

from src.config import EXCHANGES

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
    return f"{local.strftime('%-I:%M %p')} {abbr}"


def get_exchange_status(now_utc: datetime | None = None) -> dict:
    """Return open/close status for all tracked exchanges."""
    if now_utc is None:
        now_utc = datetime.now(ZoneInfo("UTC"))

    now_ts = pd.Timestamp(now_utc)
    result = {}

    for code, info in EXCHANGES.items():
        cal = _get_calendar(info["calendar"])
        tz_name = info["timezone"]

        try:
            is_open = cal.is_open_on_minute(now_ts, side="left")
        except Exception:
            is_open = False

        if is_open:
            # Find when current session closes
            session = cal.minute_to_session(now_ts, direction="none")
            close_time = cal.session_close(session)
            close_dt = close_time.to_pydatetime()
            minutes_until = max(0, int((close_dt - now_utc).total_seconds() / 60))
            result[code] = {
                "status": "open",
                "next": f"close {_format_time(close_dt, tz_name)}",
                "minutes_until": minutes_until,
            }
        else:
            # Find next open
            try:
                # Look for next valid session
                next_sessions = cal.sessions_in_range(
                    now_ts.normalize() + pd.Timedelta(days=0),
                    now_ts.normalize() + pd.Timedelta(days=7),
                )
                next_open_dt = None
                for session in next_sessions:
                    open_time = cal.session_open(session)
                    if open_time.to_pydatetime().replace(tzinfo=ZoneInfo("UTC")) > now_utc:
                        next_open_dt = open_time.to_pydatetime().replace(tzinfo=ZoneInfo("UTC"))
                        break

                if next_open_dt:
                    minutes_until = max(0, int((next_open_dt - now_utc).total_seconds() / 60))
                    result[code] = {
                        "status": "closed",
                        "next": f"open {_format_time(next_open_dt, tz_name)}",
                        "minutes_until": minutes_until,
                    }
                else:
                    result[code] = {
                        "status": "closed",
                        "next": "unknown",
                        "minutes_until": -1,
                    }
            except Exception:
                result[code] = {
                    "status": "closed",
                    "next": "unknown",
                    "minutes_until": -1,
                }

    return result
