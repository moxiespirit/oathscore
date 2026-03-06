# OathScore Alert Registry

**Last Updated**: 2026-03-05

Master inventory of every alert in the system.

---

## Alert Channel

**Telegram only** (via `alert_sender.py`). Uses `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` env vars.

No email (SendGrid has a cost). Can reuse Curistat's Telegram bot if same chat.

---

## Alert Levels

| Level | Prefix | Cooldown | Quiet Hours (12-6AM ET) | Delivery |
|-------|--------|----------|------------------------|----------|
| CRITICAL | `[CRITICAL]` | None (always sends) | Bypasses | Immediate Telegram |
| URGENT | `[URGENT]` | 1h per source:type | Bypasses | Immediate Telegram |
| WARNING | `[!!]` | 4h per source:type | Suppressed | Telegram (outside quiet hours) |
| INFO | `[i]` | 24h (buffered) | N/A | Daily digest only |

---

## All Alerts (9 types)

### Uptime Alerts
| # | Alert | Trigger | Severity | Source |
|---|-------|---------|----------|--------|
| 1 | Uptime degraded | <90% in last 60 pings | WARNING | alerts.py |
| 2 | Uptime critical | <50% in last 60 pings | URGENT | alerts.py |
| 3 | Uptime down | <30% in last 60 pings | CRITICAL | alerts.py |

### Availability Alerts
| # | Alert | Trigger | Severity | Source |
|---|-------|---------|----------|--------|
| 4 | Consecutive failures | 3+ pings fail in a row | URGENT | alerts.py |

### Freshness Alerts
| # | Alert | Trigger | Severity | Source |
|---|-------|---------|----------|--------|
| 5 | Data stale (2h) | age_seconds >7200 | WARNING | alerts.py |
| 6 | Data stale (6h) | age_seconds >21600 | URGENT | alerts.py |
| 7 | Data stale (24h) | age_seconds >86400 | CRITICAL | alerts.py |

### Schema Alerts
| # | Alert | Trigger | Severity | Source |
|---|-------|---------|----------|--------|
| 8 | Schema changed | SHA-256 hash differs | WARNING | alerts.py |

### Latency Alerts
| # | Alert | Trigger | Severity | Source |
|---|-------|---------|----------|--------|
| 9 | High latency | avg >3000ms (last 60 OK pings) | WARNING | alerts.py |

---

## Deduplication

State stored in `data/alert_dedup_state.json`:
```json
{
  "curistat:uptime_degraded": {
    "last_sent": "2026-03-05T12:00:00+00:00",
    "severity": "WARNING"
  }
}
```

**Rules**:
- Same source:type within cooldown window = suppressed
- Higher severity ALWAYS overrides cooldown (WARNING->URGENT sends immediately)
- CRITICAL has 0 cooldown (always sends)

---

## Incident Tracking

All alerts that fire also open incidents in `incident_tracker.py`:
- **Active incidents**: `data/active_incidents.json`
- **History**: `data/incident_history.jsonl` (append-only, one JSON line per event)
- **Auto-resolve**: If API passes all checks in next cycle, incident resolves with `auto_resolved: true`
- **Pattern detection**: `get_patterns(days=30)` returns APIs with 3+ incidents (repeat offenders)

---

## Daily Digest

INFO-level alerts are buffered to `data/alert_digest_buffer.json` and sent once daily as a single Telegram message. Buffer is cleared after send regardless of delivery success.

---

## Adding New Alerts

1. Add threshold check in `alerts.py` `check_alerts()`
2. Return dict with: `api`, `type`, `severity`, `message`, `value`, `timestamp`
3. `check_and_alert()` handles incident opening + Telegram delivery automatically
4. Update this registry
