"""Alert system — detects degradation, opens incidents, sends notifications."""

import logging
from datetime import datetime, timezone
from src.monitor.store import _load
from src.monitor import alert_sender, incident_tracker

logger = logging.getLogger(__name__)

# Thresholds
UPTIME_ALERT_THRESHOLD = 90.0
LATENCY_ALERT_THRESHOLD = 3000
SCHEMA_CHANGE_ALERT = True
CONSECUTIVE_FAIL_THRESHOLD = 3

# Freshness thresholds (seconds)
FRESHNESS_WARNING = 7200     # 2h
FRESHNESS_URGENT = 21600     # 6h
FRESHNESS_CRITICAL = 86400   # 24h


def check_alerts() -> list[dict]:
    """Check monitoring data for alert conditions. Returns alert list."""
    alerts = []
    pings = _load("pings.json")
    schemas = _load("schemas.json")
    freshness = _load("freshness.json")
    now = datetime.now(timezone.utc).isoformat()

    # Group recent pings by API (last 500)
    api_pings: dict[str, list] = {}
    for p in pings[-500:]:
        name = p.get("api_name")
        if name:
            api_pings.setdefault(name, []).append(p)

    for api_name, recent in api_pings.items():
        last_60 = recent[-60:]
        if len(last_60) < 5:
            continue

        # --- Uptime check ---
        ok = sum(1 for p in last_60 if p.get("ok"))
        uptime = ok / len(last_60) * 100

        if uptime < UPTIME_ALERT_THRESHOLD:
            severity = alert_sender.CRITICAL if uptime < 30 else alert_sender.URGENT if uptime < 50 else alert_sender.WARNING
            alerts.append({
                "api": api_name,
                "type": "uptime_degraded",
                "severity": severity,
                "message": f"{api_name} uptime at {uptime:.0f}% (threshold: {UPTIME_ALERT_THRESHOLD}%)",
                "value": round(uptime, 1),
                "timestamp": now,
            })

        # --- Latency check ---
        ok_latencies = [p.get("latency_ms", 0) for p in last_60 if p.get("ok")]
        if ok_latencies:
            avg = sum(ok_latencies) / len(ok_latencies)
            if avg > LATENCY_ALERT_THRESHOLD:
                alerts.append({
                    "api": api_name,
                    "type": "high_latency",
                    "severity": alert_sender.WARNING,
                    "message": f"{api_name} avg latency {avg:.0f}ms (threshold: {LATENCY_ALERT_THRESHOLD}ms)",
                    "value": round(avg),
                    "timestamp": now,
                })

        # --- Consecutive failures check ---
        tail = recent[-CONSECUTIVE_FAIL_THRESHOLD:]
        if len(tail) == CONSECUTIVE_FAIL_THRESHOLD and all(not p.get("ok") for p in tail):
            alerts.append({
                "api": api_name,
                "type": "consecutive_failures",
                "severity": alert_sender.URGENT,
                "message": f"{api_name} failed {CONSECUTIVE_FAIL_THRESHOLD} consecutive pings",
                "value": CONSECUTIVE_FAIL_THRESHOLD,
                "timestamp": now,
            })

    # --- Schema change alerts ---
    for s in schemas[-20:]:
        if s.get("changed"):
            alerts.append({
                "api": s["api_name"],
                "type": "schema_change",
                "severity": alert_sender.WARNING,
                "message": f"{s['api_name']} {s['endpoint']} response schema changed",
                "timestamp": s.get("timestamp", now),
            })

    # --- Freshness alerts ---
    # Group by API, check latest
    api_freshness: dict[str, dict] = {}
    for f in freshness:
        api_freshness[f.get("api_name", "")] = f

    for api_name, latest in api_freshness.items():
        age = latest.get("age_seconds", 0)
        if age >= FRESHNESS_CRITICAL:
            severity = alert_sender.CRITICAL
        elif age >= FRESHNESS_URGENT:
            severity = alert_sender.URGENT
        elif age >= FRESHNESS_WARNING:
            severity = alert_sender.WARNING
        else:
            continue

        hours = age / 3600
        alerts.append({
            "api": api_name,
            "type": "stale_data",
            "severity": severity,
            "message": f"{api_name} data is {hours:.1f}h stale",
            "value": round(age),
            "timestamp": now,
        })

    # Store active alerts
    from src.monitor.store import _save
    _save("active_alerts.json", alerts)
    return alerts


def check_and_alert() -> list[dict]:
    """Run alert checks, open/resolve incidents, send notifications.

    Called by scheduler after each probe cycle.
    """
    alerts = check_alerts()
    alerted_keys = set()

    for alert in alerts:
        api = alert["api"]
        atype = alert["type"]
        severity = alert["severity"]
        message = alert["message"]

        # Open incident
        incident_tracker.open_incident(api, atype, severity, message, probe_data=alert)

        # Send notification
        alert_sender.send_alert(api, atype, severity, message)
        alerted_keys.add(f"{api}:{atype}")

    # Auto-resolve: find APIs with no alerts
    all_alert_apis = {a["api"] for a in alerts}
    # Get all known API names from pings
    pings = _load("pings.json")
    all_known = {p.get("api_name") for p in pings[-500:] if p.get("api_name")}
    healthy = all_known - all_alert_apis
    incident_tracker.auto_resolve_recovered(healthy)

    return alerts
