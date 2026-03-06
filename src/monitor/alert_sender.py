"""Outbound alert notifications — Telegram only.

Adapted from Curistat's battle-tested alert_sender.py.
4 levels: INFO, WARNING, URGENT, CRITICAL.
Dedup via per-source cooldown windows. Quiet hours for low-severity.
"""

import json
import logging
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# --- Alert levels ---
INFO = "INFO"
WARNING = "WARNING"
URGENT = "URGENT"
CRITICAL = "CRITICAL"

SEVERITY_ORDER = {INFO: 0, WARNING: 1, URGENT: 2, CRITICAL: 3}

# --- Cooldown windows (seconds) per severity ---
COOLDOWN = {
    INFO: 86400,     # 24h (buffered for daily digest)
    WARNING: 14400,  # 4h
    URGENT: 3600,    # 1h
    CRITICAL: 0,     # Always send
}

# --- Quiet hours (ET): 12AM-6AM for INFO/WARNING only ---
QUIET_START = 0   # midnight
QUIET_END = 6     # 6 AM

# --- State file for dedup ---
DATA_DIR = Path(__file__).parent.parent.parent / "data"
DEDUP_FILE = DATA_DIR / "alert_dedup_state.json"
DIGEST_FILE = DATA_DIR / "alert_digest_buffer.json"


def _load_json(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return {}
    return {}


def _save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def _now_et() -> datetime:
    from zoneinfo import ZoneInfo
    return datetime.now(ZoneInfo("America/New_York"))


def _in_quiet_hours() -> bool:
    et = _now_et()
    return QUIET_START <= et.hour < QUIET_END


def _is_cooldown_active(source_key: str, severity: str) -> bool:
    """Check if this source+type is in cooldown. Higher severity overrides."""
    state = _load_json(DEDUP_FILE)
    entry = state.get(source_key)
    if not entry:
        return False

    last_sent = datetime.fromisoformat(entry["last_sent"])
    last_severity = entry.get("severity", INFO)
    elapsed = (datetime.now(timezone.utc) - last_sent).total_seconds()

    # Higher severity always overrides cooldown
    if SEVERITY_ORDER.get(severity, 0) > SEVERITY_ORDER.get(last_severity, 0):
        return False

    cooldown_secs = COOLDOWN.get(severity, 14400)
    return elapsed < cooldown_secs


def _record_sent(source_key: str, severity: str):
    state = _load_json(DEDUP_FILE)
    state[source_key] = {
        "last_sent": datetime.now(timezone.utc).isoformat(),
        "severity": severity,
    }
    _save_json(DEDUP_FILE, state)


def _send_telegram(message: str, severity: str) -> bool:
    """Send via Telegram Bot API using urllib (no extra deps)."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        logger.debug("Telegram not configured, skipping")
        return False

    prefix = {"INFO": "i", "WARNING": "!!", "URGENT": "URGENT", "CRITICAL": "CRITICAL"}.get(severity, "")
    text = f"[{prefix}] *OathScore {severity}*\n{message}"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }).encode()

    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        logger.error("Telegram send failed: %s", e)
        return False


def send_alert(api_name: str, alert_type: str, severity: str, message: str) -> bool:
    """Send an alert with dedup and quiet hours.

    Returns True if alert was actually sent (not suppressed).
    """
    source_key = f"{api_name}:{alert_type}"
    sev = severity.upper()

    # Buffer INFO for daily digest
    if sev == INFO:
        _buffer_digest(api_name, alert_type, message)
        return False

    # Quiet hours suppress WARNING
    if _in_quiet_hours() and sev == WARNING:
        logger.debug("Quiet hours, suppressing WARNING for %s", source_key)
        return False

    # Dedup cooldown check
    if _is_cooldown_active(source_key, sev):
        logger.debug("Cooldown active for %s at %s", source_key, sev)
        return False

    # Send via Telegram
    sent = _send_telegram(f"{api_name}: {message}", sev)

    if sent:
        _record_sent(source_key, sev)
        logger.info("Alert sent [%s] %s: %s", sev, source_key, message)
        return True

    logger.warning("Alert delivery failed for %s", source_key)
    return False


def _buffer_digest(api_name: str, alert_type: str, message: str):
    """Buffer an INFO alert for daily digest."""
    buf = _load_json(DIGEST_FILE)
    items = buf.get("items", [])
    items.append({
        "api_name": api_name,
        "type": alert_type,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    buf["items"] = items
    _save_json(DIGEST_FILE, buf)


def send_daily_digest() -> bool:
    """Send buffered INFO alerts as a single digest. Call once daily."""
    buf = _load_json(DIGEST_FILE)
    items = buf.get("items", [])
    if not items:
        return False

    lines = [f"- [{i['api_name']}] {i['message']}" for i in items[-50:]]
    body = f"OathScore Daily Digest ({len(items)} events)\n\n" + "\n".join(lines)

    sent = _send_telegram(body, INFO)

    # Clear buffer regardless
    _save_json(DIGEST_FILE, {"items": [], "last_sent": datetime.now(timezone.utc).isoformat()})
    return sent
