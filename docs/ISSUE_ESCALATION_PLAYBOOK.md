# OathScore Issue Escalation Playbook

**Last Updated**: 2026-03-05

Decision tree + predetermined fixes for known failure scenarios.

---

## Severity Levels

| Level | Definition | Response Time | Notification |
|-------|-----------|---------------|--------------|
| SEV-1 CRITICAL | Service down, data corruption, security breach | Immediate | Telegram (bypasses quiet hours + dedup) |
| SEV-2 URGENT | API source dead, scoring broken, billing failure | Within 4h | Telegram (bypasses quiet hours) |
| SEV-3 WARNING | Single API degraded, stale data <6h, schema change | Within 24h | Telegram (suppressed during quiet hours 12-6AM ET) |
| SEV-4 INFO | Minor degradation, informational | Next session | Buffered for daily digest |

## Auto-Escalation

3+ consecutive alert cycles (15 min) for the same source at WARNING -> auto-escalates to URGENT via incident_tracker severity upgrade.

---

## Known Scenarios & Predetermined Fixes

### API-1: Alpha Vantage Rate Limited (HTTP 429)
- **Severity**: WARNING (single source)
- **Symptoms**: Ping failures, 429 status codes
- **Fix**: Nothing — free tier is 25 requests/day. Probes will naturally hit this limit. If persistent, reduce probe frequency for this API or upgrade AV plan.
- **Workaround**: None needed. Scoring handles missing data by reweighting.

### API-2: Polygon.io Key Expired
- **Severity**: URGENT (all Polygon probes fail)
- **Symptoms**: 403 on all Polygon endpoints
- **Fix**: Regenerate key at https://polygon.io/dashboard/api-keys. Update `POLYGON_KEY` in Railway. Redeploy.

### API-3: Finnhub Rate Limited
- **Severity**: WARNING
- **Symptoms**: 429 responses, free tier = 60 calls/min
- **Fix**: Probe runs every 60s (2 endpoints = 2 calls/min). Should not hit limit. If it does, check for duplicate scheduler instances.

### API-4: Yahoo Finance Blocking
- **Severity**: URGENT (affects accuracy verification)
- **Symptoms**: 403 or empty responses from query1.finance.yahoo.com
- **Fix**: Yahoo periodically blocks server IPs. accuracy_probe.py verify step will fail. Wait 24h or change User-Agent string in accuracy_probe.py.

### API-5: Curistat Down
- **Severity**: CRITICAL (only source with forecast accuracy data)
- **Symptoms**: /health returns non-200 or timeout on curistat-api-production.up.railway.app
- **Fix**: Check Curistat Railway dashboard. If Railway outage, wait. If code issue, check Curistat's own logs.
- **Impact**: Accuracy scoring (35% weight) becomes unavailable. Composite scores reweight around remaining components.

### API-6: FRED 403 (Key Issue)
- **Severity**: URGENT
- **Symptoms**: 403 on /fred/series/observations
- **Fix**: Verify FRED_KEY in Railway. Regenerate at https://fredaccount.stlouisfed.org/apikeys if needed. FRED occasionally has maintenance windows.

### API-7: Supabase Unreachable
- **Severity**: WARNING (local storage still works)
- **Symptoms**: Supabase insert/query calls fail, logged as errors
- **Fix**: Check https://status.supabase.com. If project paused (free tier inactivity), reactivate in Supabase dashboard. Local JSON continues working — no data loss.

### API-8: Railway Deploy Fails
- **Severity**: CRITICAL (service goes offline)
- **Symptoms**: `railway up` fails, or service crashes on startup
- **Fix**: Check Docker build logs in Railway dashboard. Common causes: missing env var, dependency version conflict, syntax error.
- **Rollback**: Railway keeps previous deploys. Use Railway dashboard to redeploy last working version.

### API-9: Stripe Webhook Fails
- **Severity**: URGENT (billing broken)
- **Symptoms**: Stripe dashboard shows failed webhook deliveries
- **Fix**: Verify `STRIPE_WEBHOOK_SECRET` matches. Check Railway logs for webhook endpoint errors. Test with `stripe trigger checkout.session.completed`.

### API-10: Kill Switch Activated (Intentional)
- **Severity**: N/A (intentional)
- **Symptoms**: All endpoints except /health return 503
- **Fix**: Remove or set `{"active": false}` in `data/kill_switch.json`. Redeploy or restart.

---

## General Troubleshooting

### Probe Not Running
- Check Railway logs for "Running X probe" messages
- If missing, scheduler may have crashed — redeploy
- Each probe is independent; one crash doesn't affect others

### No Scores Generating
- Need 10+ pings before scoring starts (10 min after deploy)
- Need 5+ verified forecasts for accuracy component (5+ days)
- Check `curl https://api.oathscore.dev/score/curistat` — should show components or "monitoring" message

### Alert Spam
- Check `data/alert_dedup_state.json` for cooldown state
- WARNING cooldown = 4h, URGENT = 1h
- If legitimate repeated failures, investigate root cause instead of suppressing

### Data Files Missing
- `data/monitor/` is gitignored — fresh deploy starts with empty data
- This is expected. Probes will repopulate within minutes.
- Supabase has persistent history if needed.

---

## Unknown Failure Triage (Generic)

When you hit a failure mode NOT listed above, follow this checklist in order:

### Step 1: Identify the scope
- Is it one API or all APIs?
- Is it one probe or all probes?
- Is it the OathScore API itself or a monitored API?

### Step 2: Check OathScore health
```bash
curl -s https://api.oathscore.dev/health
```
- If DOWN → Railway issue. Check Railway dashboard for deploy failures, memory limits, or outage.
- If UP but returning errors → check Railway logs: `railway logs --limit 50`

### Step 3: Check upstream status pages
- Railway: https://status.railway.app
- Supabase: https://status.supabase.com
- GitHub: https://www.githubstatus.com
- Cloudflare: https://www.cloudflarestatus.com

### Step 4: Check env vars
```bash
railway variables 2>/dev/null
```
Compare against `src/monitor/config.py` key_env values. A changed or deleted env var can silently break an entire probe.

### Step 5: Check recent deploys
```bash
git log --oneline -5
```
Did a recent deploy introduce the issue? If so, rollback in Railway dashboard.

### Step 6: Check Railway logs for patterns
```bash
railway logs --limit 100 2>/dev/null | grep -iE "error|exception|traceback|timeout"
```

### Step 7: Check incident history
Review `data/incident_history.jsonl` (if accessible) for similar past incidents. Check `docs/ISSUE_ESCALATION_PLAYBOOK.md` for known scenarios that may have been added since this section was written.

### Step 8: Escalate
If none of the above identifies the issue:
1. Send URGENT Telegram alert (if alert system is working)
2. Create GitHub issue with `waiting-owner` label
3. Document findings in `tracking/OWNER_NOTES.md`
4. If service is critically impaired, activate kill switch: write `{"active": true, "reason": "investigating unknown failure"}` to `data/kill_switch.json`
