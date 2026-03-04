"""Example: Continuous Market Monitor using OathScore.

Polls OathScore every 60 seconds and alerts on regime changes.
Demonstrates the /now endpoint for real-time monitoring.

Usage:
    pip install httpx
    python examples/market_monitor.py
"""

import time
import httpx

OATHSCORE_URL = "https://api.oathscore.dev"

# Track state changes
_last_vix = None
_last_term = None
_last_open = set()


def check_and_alert():
    """Poll OathScore and alert on changes."""
    global _last_vix, _last_term, _last_open

    try:
        resp = httpx.get(f"{OATHSCORE_URL}/now", timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[ERROR] Failed to fetch: {e}")
        return

    vol = data.get("volatility", {})
    exchanges = data.get("exchanges", {})
    events = data.get("events", {})

    vix = vol.get("vix")
    term = vol.get("term_structure")
    currently_open = {name for name, info in exchanges.items() if info.get("status") == "open"}

    ts = data.get("timestamp", "")[:19]

    # VIX threshold alerts
    if vix and _last_vix:
        if vix > 25 and _last_vix <= 25:
            print(f"[{ts}] ALERT: VIX crossed above 25 ({_last_vix} -> {vix})")
        elif vix < 20 and _last_vix >= 20:
            print(f"[{ts}] ALERT: VIX dropped below 20 ({_last_vix} -> {vix})")
        elif abs(vix - _last_vix) > 2:
            print(f"[{ts}] VIX moved: {_last_vix} -> {vix}")

    # Term structure change
    if term and term != _last_term and _last_term is not None:
        print(f"[{ts}] ALERT: Term structure changed: {_last_term} -> {term}")

    # Exchange open/close transitions
    if _last_open:
        opened = currently_open - _last_open
        closed = _last_open - currently_open
        for ex in opened:
            print(f"[{ts}] {ex} OPENED")
        for ex in closed:
            print(f"[{ts}] {ex} CLOSED")

    # Event countdown
    next_event = events.get("next_event")
    hours = events.get("hours_until_next_event", 999)
    if next_event and hours < 2:
        print(f"[{ts}] EVENT APPROACHING: {next_event} in {hours:.1f} hours")

    # Update state
    _last_vix = vix
    _last_term = term
    _last_open = currently_open

    # Status line
    open_str = ",".join(sorted(currently_open)) if currently_open else "none"
    print(f"[{ts}] VIX={vix} term={term} open=[{open_str}]")


def main():
    print("OathScore Market Monitor")
    print("Polling every 60 seconds. Ctrl+C to stop.\n")

    while True:
        check_and_alert()
        time.sleep(60)


if __name__ == "__main__":
    main()
