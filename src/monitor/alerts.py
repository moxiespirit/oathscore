"""Alert system — detects degradation and notifies."""

import logging
from datetime import datetime, timezone
from src.monitor.store import _load, _save

logger = logging.getLogger(__name__)

# Thresholds for alerting
UPTIME_ALERT_THRESHOLD = 90.0  # Alert if uptime drops below 90%
LATENCY_ALERT_THRESHOLD = 3000  # Alert if avg latency exceeds 3s
SCHEMA_CHANGE_ALERT = True  # Alert on any schema change


def check_alerts() -> list[dict]:
    """Check monitoring data for alert conditions."""
    alerts = []
    pings = _load("pings.json")
    schemas = _load("schemas.json")
    now = datetime.now(timezone.utc).isoformat()

    # Group recent pings by API (last 60 pings = ~1 hour)
    api_pings: dict[str, list] = {}
    for p in pings[-500:]:
        name = p.get("api_name")
        if name:
            api_pings.setdefault(name, []).append(p)

    for api_name, recent in api_pings.items():
        last_60 = recent[-60:]
        if len(last_60) < 5:
            continue

        ok = sum(1 for p in last_60 if p.get("ok"))
        uptime = ok / len(last_60) * 100

        if uptime < UPTIME_ALERT_THRESHOLD:
            alerts.append({
                "api": api_name,
                "type": "uptime_degraded",
                "severity": "high" if uptime < 50 else "medium",
                "message": f"{api_name} uptime at {uptime:.0f}% (threshold: {UPTIME_ALERT_THRESHOLD}%)",
                "value": round(uptime, 1),
                "timestamp": now,
            })

        ok_latencies = [p.get("latency_ms", 0) for p in last_60 if p.get("ok")]
        if ok_latencies:
            avg = sum(ok_latencies) / len(ok_latencies)
            if avg > LATENCY_ALERT_THRESHOLD:
                alerts.append({
                    "api": api_name,
                    "type": "high_latency",
                    "severity": "medium",
                    "message": f"{api_name} avg latency {avg:.0f}ms (threshold: {LATENCY_ALERT_THRESHOLD}ms)",
                    "value": round(avg),
                    "timestamp": now,
                })

    # Schema change alerts
    for s in schemas[-20:]:
        if s.get("changed"):
            alerts.append({
                "api": s["api_name"],
                "type": "schema_change",
                "severity": "high",
                "message": f"{s['api_name']} {s['endpoint']} response schema changed",
                "timestamp": s.get("timestamp", now),
            })

    # Store active alerts
    _save("active_alerts.json", alerts)
    return alerts
