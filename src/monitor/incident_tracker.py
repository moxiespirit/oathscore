"""Persistent incident lifecycle tracking.

Incidents: OPEN -> INVESTIGATING -> RESOLVED (or auto-resolved on recovery).
History stored as append-only JSONL at data/incident_history.jsonl.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

# --- State files ---
DATA_DIR = Path(__file__).parent.parent.parent / "data"
HISTORY_FILE = DATA_DIR / "incident_history.jsonl"
ACTIVE_FILE = DATA_DIR / "active_incidents.json"

# Statuses
OPEN = "open"
INVESTIGATING = "investigating"
RESOLVED = "resolved"


def _load_active() -> dict[str, dict]:
    """Load active incidents keyed by 'api_name:incident_type'."""
    if ACTIVE_FILE.exists():
        try:
            return json.loads(ACTIVE_FILE.read_text())
        except Exception:
            return {}
    return {}


def _save_active(incidents: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ACTIVE_FILE.write_text(json.dumps(incidents, indent=2))


def _append_history(event: dict):
    """Append one event line to JSONL history."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def open_incident(api_name: str, incident_type: str, severity: str, message: str, probe_data: dict | None = None) -> dict:
    """Open a new incident or return existing one if already open."""
    key = f"{api_name}:{incident_type}"
    active = _load_active()

    if key in active:
        # Already open — update severity if escalated
        existing = active[key]
        from src.monitor.alert_sender import SEVERITY_ORDER
        if SEVERITY_ORDER.get(severity, 0) > SEVERITY_ORDER.get(existing.get("severity", "INFO"), 0):
            existing["severity"] = severity
            existing["message"] = message
            existing["updated_at"] = _now_iso()
            active[key] = existing
            _save_active(active)
            _append_history({"event": "escalated", "key": key, **existing})
        return existing

    incident = {
        "api_name": api_name,
        "incident_type": incident_type,
        "severity": severity,
        "message": message,
        "status": OPEN,
        "opened_at": _now_iso(),
        "updated_at": _now_iso(),
        "probe_data": probe_data,
    }
    active[key] = incident
    _save_active(active)
    _append_history({"event": "opened", "key": key, **incident})
    logger.info("Incident opened: %s — %s", key, message)
    return incident


def resolve_incident(api_name: str, incident_type: str, auto: bool = False) -> dict | None:
    """Resolve an active incident. Returns the resolved incident or None."""
    key = f"{api_name}:{incident_type}"
    active = _load_active()

    if key not in active:
        return None

    incident = active.pop(key)
    opened_at = datetime.fromisoformat(incident["opened_at"])
    resolution_minutes = (datetime.now(timezone.utc) - opened_at).total_seconds() / 60

    incident["status"] = RESOLVED
    incident["resolved_at"] = _now_iso()
    incident["resolution_time_minutes"] = round(resolution_minutes, 1)
    incident["auto_resolved"] = auto

    _save_active(active)
    _append_history({"event": "resolved", "key": key, **incident})
    logger.info("Incident resolved: %s (%.1f min, auto=%s)", key, resolution_minutes, auto)
    return incident


def auto_resolve_recovered(healthy_apis: set[str]):
    """Check active incidents — resolve any whose API is now healthy.

    Call after each probe cycle with the set of APIs that passed all checks.
    """
    active = _load_active()
    to_resolve = []
    for key, incident in active.items():
        if incident["api_name"] in healthy_apis:
            to_resolve.append((incident["api_name"], incident["incident_type"]))

    for api_name, itype in to_resolve:
        resolve_incident(api_name, itype, auto=True)


def get_active_incidents() -> list[dict]:
    """Return all currently open incidents."""
    active = _load_active()
    return list(active.values())


def get_patterns(days: int = 30) -> dict[str, int]:
    """Return APIs with 3+ incidents in the last N days (repeat offenders)."""
    if not HISTORY_FILE.exists():
        return {}

    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    counts: dict[str, int] = {}

    with open(HISTORY_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except Exception:
                continue
            if event.get("event") != "opened":
                continue
            if event.get("opened_at", "") < cutoff:
                continue
            api = event.get("api_name", "unknown")
            counts[api] = counts.get(api, 0) + 1

    return {api: count for api, count in counts.items() if count >= 3}


def get_source_health(api_name: str) -> dict:
    """Return uptime %, incident count, mean resolution time for an API."""
    if not HISTORY_FILE.exists():
        return {"uptime_pct": 100.0, "incident_count": 0, "mean_resolution_minutes": 0}

    incidents = []
    with open(HISTORY_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except Exception:
                continue
            if event.get("api_name") != api_name:
                continue
            if event.get("event") == "resolved":
                incidents.append(event)

    if not incidents:
        return {"uptime_pct": 100.0, "incident_count": 0, "mean_resolution_minutes": 0}

    total_downtime = sum(i.get("resolution_time_minutes", 0) for i in incidents)
    count = len(incidents)
    # Rough uptime: assume 30-day window
    total_minutes = 30 * 24 * 60
    uptime = max(0, 100 * (1 - total_downtime / total_minutes))

    return {
        "uptime_pct": round(uptime, 2),
        "incident_count": count,
        "mean_resolution_minutes": round(total_downtime / count, 1) if count else 0,
    }
