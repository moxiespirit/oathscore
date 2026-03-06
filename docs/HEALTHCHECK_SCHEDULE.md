# OathScore Healthcheck Schedule

**Last Updated**: 2026-03-05

Every scheduled check, what failure looks like, and what to do about it.

---

## Background Probes (scheduler.py)

All probes run as asyncio tasks inside FastAPI lifespan. They start on deploy and run continuously.

| ID | Probe | Interval | File | What It Checks |
|----|-------|----------|------|----------------|
| P1 | Ping | 60s | `ping_probe.py` | HTTP GET to each API's health/sample endpoint. Records status code, latency_ms, ok boolean. |
| P2 | Freshness | 300s (5m) | `freshness_probe.py` | Extracts timestamp from API response, computes age_seconds. Looks for `timestamp`, `updated_at`, `last_updated`, `date`, etc. |
| P3 | Schema | 3600s (1h) | `schema_probe.py` | SHA-256 hash of response structure (keys + types). Compares to previous hash. |
| P4 | Snapshot | 3600s (1h) | `accuracy_probe.py` | Captures Curistat forecast value + date for later verification. |
| P5 | Verify | 86400s (24h) | `accuracy_probe.py` | Compares yesterday's forecast snapshot against actual (Yahoo Finance). Computes accuracy_score. |
| P6 | Docs | 86400s (24h) | `docs_probe.py` | Checks 5 discovery files: `/openapi.json`, `/llms.txt`, `/llms-full.txt`, `/.well-known/ai-plugin.json`, `/robots.txt`. |
| P7 | Daily Scores | 86400s (24h) | `scoring.py` | Computes composite 0-100 score for each API, persists to Supabase `daily_scores` table. |

## Alert Checks (NEW — alerts.py + scheduler.py)

| ID | Check | Interval | What It Does |
|----|-------|----------|--------------|
| A1 | Alert Check | 300s (5m) | Runs `check_and_alert()`: threshold checks -> open/resolve incidents -> send Telegram |
| A2 | Daily Digest | 86400s (24h) | Sends buffered INFO alerts as single Telegram message |

## External Checks

| ID | Check | Interval | Where |
|----|-------|----------|-------|
| E1 | GitHub Actions health check | Every 6h | `.github/workflows/health-check.yml` |
| E2 | GitHub Actions schema validation | Every 6h | Same workflow — validates /now has required fields |

---

## Alert Thresholds (alerts.py)

| Condition | Threshold | Severity | Alert Type |
|-----------|-----------|----------|------------|
| Uptime degraded | <90% (last 60 pings) | WARNING | `uptime_degraded` |
| Uptime critical | <50% | URGENT | `uptime_degraded` |
| Uptime down | <30% | CRITICAL | `uptime_degraded` |
| High latency | avg >3000ms | WARNING | `high_latency` |
| Consecutive failures | 3+ pings fail in a row | URGENT | `consecutive_failures` |
| Data stale (2h) | age_seconds >7200 | WARNING | `stale_data` |
| Data stale (6h) | age_seconds >21600 | URGENT | `stale_data` |
| Data stale (24h) | age_seconds >86400 | CRITICAL | `stale_data` |
| Schema changed | hash differs from previous | WARNING | `schema_change` |

---

## Failure Handling

Each probe is wrapped in try/except. A failing probe does NOT block other probes.

**Storage resilience**: Every probe dual-writes to local JSON + Supabase. Supabase failure is logged but doesn't block local write.

**Alert delivery**: If Telegram fails, alert is logged but not retried (next cycle will re-detect and re-attempt).

**Incident auto-resolve**: After each alert check, APIs with no active alerts are checked against open incidents. Recovered APIs get incidents auto-resolved.

---

## What to Check Manually

### Daily (if no paying customers yet)
- `curl https://api.oathscore.dev/health` — should return `{"status": "ok"}`
- `curl https://api.oathscore.dev/alerts` — review active alerts
- Check Railway logs for probe errors

### Weekly
- Review `data/incident_history.jsonl` for patterns
- Check Supabase dashboard for data growth
- Verify GitHub Actions health check is green

### After Deploy
- Hit `/health`, `/now`, `/scores`, `/alerts` — all should return 200
- Check Railway logs for startup errors
- Verify all 7 probe loops are running (look for "Running X probe" in logs)
