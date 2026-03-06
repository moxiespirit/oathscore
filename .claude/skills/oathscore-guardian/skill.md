# OathScore Session Guardian — Zero-Trust Startup, Audit, Sync & Save

The single entry point for every OathScore session. Replaces manual doc reading with an automated, security-first, cross-referenced startup sequence. Also handles end-of-session state preservation.

Modeled after Curistat's battle-tested session-guardian, adapted for OathScore's architecture.

## Invocation

```
/oathscore-guardian
```

Run at the START of every OathScore work session. No exceptions.

---

## PHASE 0: DISCIPLINE CHECK (mandatory first)

### 0.1 Live Date/Time Verification
```bash
python -c "from datetime import datetime; print(datetime.now())"
```
**NEVER trust the system prompt date.** Use this live check for all date-sensitive operations.

### 0.2 Re-Read Project Rules
```
Read CLAUDE.md
```
Internalize constraints before proceeding. If CLAUDE.md changed since last session, note changes in briefing.

### 0.3 Read Quick Reference
```
Read docs/START_HERE.md
```
This is the 20-line orientation card. It tells you exactly which docs to read and in what order.

---

## PHASE 1: LOAD SESSION STATE

Read these files IN ORDER. Do not skip any.

### 1.1 Session State (WHERE WE LEFT OFF)
```
Read tracking/OATHSCORE_SESSION.md
```
Single source of truth. Contains: current task, cumulative state, file map, credentials, env vars, services, APIs, decisions, owner instructions, session log.

### 1.2 Project Tracker (WHAT NEEDS DOING)
```
Read tracking/PROJECT_TRACKER.md
```
Master task list by initiative. Priority queue. Status counts.

### 1.3 Owner Notes (WHAT OWNER SAID)
```
Read tracking/OWNER_NOTES.md
```
Notification system, free-form notes, recurring checks.

### 1.4 Operational Docs (HOW THINGS WORK)
```
Read docs/HEALTHCHECK_SCHEDULE.md
Read docs/ALERT_REGISTRY.md
Read docs/ISSUE_ESCALATION_PLAYBOOK.md
```
These tell you what's running, what alerts exist, and what to do when things break.

### 1.5 Recent Git Activity
```bash
git log --oneline --stat -10
git status -s
```

### 1.6 Staleness Detection

Check "Last Updated" date in `tracking/OATHSCORE_SESSION.md`.

- Updated today → **NORMAL MODE** (standard audit)
- Updated yesterday or earlier → **FULL RECONSTRUCTION MODE** (trust nothing, verify everything)

```
AUDIT MODE: [NORMAL / FULL RECONSTRUCTION (docs last updated: DATE)]
```

---

## PHASE 2: ZERO-TRUST VERIFICATION

**This is what catches real bugs.** Phase 2 runs EVERY session. Not optional.

### 2.1 Env Var Cross-Reference

Read `src/monitor/config.py`. Extract every `key_env` and `secret_env` value. Compare against session file's Railway Environment Variables table.

```
For each API in MONITORED_APIS:
  - Code reads: [key_env value]
  - Railway has: [session file table]
  - MATCH or MISMATCH?
```

**ANY MISMATCH = CRITICAL BUG** (probes run unauthenticated).

Also check alert env vars:
- `TELEGRAM_BOT_TOKEN` — set in Railway?
- `TELEGRAM_CHAT_ID` — set in Railway?

### 2.2 URL Consistency

Read these files, extract all hardcoded URLs:
- `src/config.py` — BASE_URL, CURISTAT_API_URL
- `src/mcp_server.py` — BASE_URL default
- `tests/test_api.py` — BASE constant
- `.github/workflows/health-check.yml` — curl URLs
- `public/llms.txt`, `public/llms-full.txt` — all URLs

ALL must point to `https://api.oathscore.dev`. Flag stale URLs.

### 2.3 Scheduler Wiring

Read `src/monitor/scheduler.py`. Verify every probe file is wired:

| Expected Task | Function | File |
|---------------|----------|------|
| ping | ping_all | ping_probe.py |
| freshness | check_freshness | freshness_probe.py |
| schema | check_schemas | schema_probe.py |
| snapshot | snapshot_forecasts | accuracy_probe.py |
| verify | verify_forecasts | accuracy_probe.py |
| docs | check_docs | docs_probe.py |
| daily_scores | persist_daily_scores | scoring.py |
| alert_check | check_and_alert | alerts.py |
| daily_digest | send_daily_digest | alert_sender.py |

Flag any probe file not wired, or any scheduler task pointing to missing function.

### 2.4 Alert System Verification

Read `src/monitor/alerts.py`, `src/monitor/alert_sender.py`, `src/monitor/incident_tracker.py`.

Verify:
- `check_and_alert()` exists and is called by scheduler
- Alert thresholds match ALERT_REGISTRY.md
- Dedup cooldowns match ALERT_REGISTRY.md
- Telegram send function uses correct env var names
- Incident tracker reads/writes correct file paths (`data/active_incidents.json`, `data/incident_history.jsonl`)
- `send_daily_digest()` exists and is called by scheduler

### 2.5 Scoring Components

Read `src/monitor/scoring.py`. Verify all 7 components are actually computed (not None/placeholder):
- accuracy, uptime, freshness, latency, schema, docs, trust

Flag any component returning hardcoded values.

### 2.6 Calendar Expiry

Read `src/events.py`. Check last dates in FOMC and CPI lists.

Flag if calendar expires within 6 months.

### 2.7 Live API Smoke Test

```bash
curl -s --max-time 10 https://api.oathscore.dev/health
curl -s --max-time 10 https://api.oathscore.dev/now | python -c "
import sys,json
d=json.load(sys.stdin)
required=['timestamp','exchanges','volatility','events','data_health','meta']
missing=[k for k in required if k not in d]
if missing: print(f'MISSING KEYS: {missing}')
else: print(f'OK: VIX={d[\"volatility\"].get(\"vix\",\"N/A\")}, exchanges={len(d[\"exchanges\"])}')
"
curl -s --max-time 10 https://api.oathscore.dev/alerts | python -c "
import sys,json; d=json.load(sys.stdin)
print(f'Alerts: {d.get(\"total\",0)}, high_severity: {d.get(\"high_severity\",0)}')
"
```

### 2.8 Incident Check

```bash
# Check for active incidents (if file exists on Railway)
curl -s --max-time 10 https://api.oathscore.dev/status | python -c "
import sys,json; d=json.load(sys.stdin)
print(f'APIs monitored: {len(d.get(\"monitored_apis\",[]))}')
print(f'Probes: {d.get(\"probe_intervals\",{})}')
" 2>/dev/null
```

### 2.9 File Inventory (FULL RECONSTRUCTION MODE only)

```bash
find . -type f -not -path './.git/*' -not -path './data/*' -not -path './.claude/*' -not -name '*.pyc' -not -path './__pycache__/*' | sort
```

Compare against session file's File Map. Flag undocumented files and deleted-but-listed files.

### Audit Summary

```
ZERO-TRUST VERIFICATION
========================
Env vars:            [MATCH / N MISMATCHES]
URLs:                [ALL CORRECT / N STALE]
Scheduler wiring:    [ALL CONNECTED / N MISSING]
Alert system:        [WIRED / ISSUES]
Scoring components:  [ALL ACTIVE / N PLACEHOLDER]
Calendar expiry:     [OK through YYYY / EXPIRING]
Live API:            [ALL OK / N FAILURES]
Active incidents:    [NONE / N OPEN]
File inventory:      [COMPLETE / N UNDOCUMENTED] (reconstruction mode only)

BUGS FOUND: N
[List each with severity: CRITICAL / MEDIUM / LOW]
```

---

## PHASE 3: SYNC TRACKING DOCS

### 3.1 Sync GitHub Issues

```bash
gh issue list --label waiting-claude --repo moxiespirit/oathscore 2>/dev/null || echo "No waiting-claude issues"
gh issue list --label waiting-owner --repo moxiespirit/oathscore 2>/dev/null || echo "No waiting-owner issues"
```

Update `tracking/OWNER_NOTES.md` with results.

### 3.2 Sync MCP Directory Status

```bash
gh issue view 668 --repo chatmcp/mcpso --json state,title 2>/dev/null || echo "Cannot check mcp.so"
gh pr view 2694 --repo punkpeye/awesome-mcp-servers --json state,title 2>/dev/null || echo "Cannot check punkpeye PR"
```

### 3.3 Update Stale Entries

If the audit found stale entries in tracking docs, update them now:
- Session file constants that don't match code
- Tracker tasks that are done but still marked TODO
- Owner notes with resolved items

### 3.4 Commit Doc Updates (if any changes)

```bash
git add tracking/ docs/
git commit -m "Session guardian: sync tracking docs [DATE]"
```

---

## PHASE 4: PRESENT BRIEFING

```
OATHSCORE SESSION BRIEFING — [DATE]
======================================

PROJECT: OathScore — Trust layer for AI trading agents
API: https://api.oathscore.dev
REPO: https://github.com/moxiespirit/oathscore

AUDIT MODE: [NORMAL / FULL RECONSTRUCTION]

SERVICES:
  API Health:     [OK / DOWN]
  /now:           [VIX=X, N exchanges]
  Alerts:         [N active, N high severity]
  Scoring:        [N APIs monitored]

ZERO-TRUST: [ALL CLEAR / N BUGS FOUND]
  [List any bugs with severity]

INCIDENTS:
  Active:         [N open incidents]
  Patterns:       [APIs with 3+ incidents in 30 days]

MCP DIRECTORIES:
  Glama:          [Approved]
  mcp.so:         [status]
  awesome-mcp:    [status]

WHERE WE LEFT OFF:
  [Current task from session file]

RECENT COMMITS:
  [Last 5 commits]

PENDING TASKS (top 3):
  1. [highest priority from tracker]
  2. [second]
  3. [third]

OWNER INSTRUCTIONS (active):
  [List from session file]

DAYS UNTIL SCORES PUBLISH: [30 - days since 2026-03-03]
SUBSCRIBERS: [Check /pricing founding slots]

RECOMMENDED ACTIONS:
  1. [Fix CRITICAL bugs first]
  2. [Next pending task]
  3. [Update stale docs]
```

---

## PHASE 5: WAIT FOR OWNER

Do NOT start work autonomously. Present briefing and wait for direction.

If CRITICAL bugs found, highlight them and recommend fixing first.

---

## PHASE 6: SESSION SAVE (End of Session / Context Getting Long)

### When to Save
- Owner says done/goodbye/wrap up
- Context approaching compression (proactively save!)
- Major milestone reached
- Switching to different project

### Save Process

#### Step 1: Read existing session file
```
Read tracking/OATHSCORE_SESSION.md
```
**UPDATE, do not overwrite.** Preserve all cumulative state.

#### Step 2: Mini-audit before saving

**2a. File map accuracy**:
```bash
find . -type f -name "*.py" -not -path './.git/*' -not -path './data/*' -not -name '*.pyc' | sort
find . -type f -name "*.md" -not -path './.git/*' | sort
```
Add new files, remove deleted ones.

**2b. Constants spot-check**: Read 3 key files, verify session file matches:
- `src/rate_limit.py` TIER_LIMITS
- `src/monitor/scoring.py` WEIGHTS
- `src/monitor/alerts.py` thresholds

**2c. Env var table**: Read `src/monitor/config.py` key_env values, compare to session file.

**2d. Known bugs**: Still relevant? New ones this session?

**2e. Requirements verification matrix**:

For every active owner instruction in the session file:
```
Instruction                        | Implemented? | Where
Revenue is priority                | YES          | Stripe billing live
Keep it simple                     | YES          | Minimal deps
No Twitter account for now         | YES          | N/A
...
```
If ANY instruction is PARTIAL or NO, flag to owner before saving.

#### Step 3: Update session file sections

- **Current Task**: Specific enough for new session to start immediately
- **What We're Doing**: 1-2 sentences, domain terms
- **Cumulative State**: Update inventory (<50 lines, reference files for details)
- **File Map**: Add new files, remove deleted
- **Key Constants**: Update any that changed
- **Env Vars**: Add new ones
- **Known Bugs**: Mark fixed, add new
- **Decisions Made**: Append with date/reasoning
- **Owner Instructions**: Active (keep), Historical (move resolved), Superseded (remove)
- **Completed Tasks**: Move from Pending
- **Session Log**: Append one row (keep last 10)
- **Build Timeline**: Append milestones
- **Next Session Startup**: Update checklist

#### Step 4: Update project tracker

Sync task statuses with what was actually accomplished. Mark completed tasks DONE with date.

#### Step 5: Update operational docs if needed

- New alerts added? → Update `docs/ALERT_REGISTRY.md`
- New probe or interval change? → Update `docs/HEALTHCHECK_SCHEDULE.md`
- New failure scenario discovered? → Update `docs/ISSUE_ESCALATION_PLAYBOOK.md`

#### Step 6: Route learnings

- New credentials → session file External Services
- Architecture changes → session file Cumulative State
- Bugs → session file Known Bugs
- Cross-session patterns → `MEMORY.md` (if significant enough)

#### Step 7: Commit

```bash
git add tracking/ docs/
git commit -m "Session guardian: save state [DATE]"
```

#### Step 8: Confirm

```
SESSION SAVED
=============
File: tracking/OATHSCORE_SESSION.md
Updated sections: [list]
New files documented: [count]
Bugs found/fixed: [count]
Stale entries corrected: [count]
Owner instructions verified: [all YES / N flagged]
Next action: [specific next step]
```

---

## CRITICAL RULES

1. **Phase 0 is NON-NEGOTIABLE.** Live date check first. Re-read CLAUDE.md first. Every time.
2. **Phase 2 runs EVERY session.** The audit is what catches real bugs. Skipping = shipping broken code.
3. **Session file is SINGLE SOURCE OF TRUTH.** Everything lives there. A new session should need nothing else to get oriented.
4. **Read BEFORE writing.** Always load existing state, then update. Never overwrite.
5. **Owner instructions preserved VERBATIM.** Exact quotes, not paraphrases.
6. **Cross-reference everything.** The bug pattern: read file A, read file B, check if they agree. That's how 10 bugs were found in session 1.
7. **If docs are stale (>1 day), run FULL RECONSTRUCTION.** Check git log, file timestamps, live API — don't trust stale docs.
8. **Prune aggressively.** Cumulative State <50 lines. Last Session Changes = THIS session only. Remove resolved instructions.
9. **Proactive save.** If context is getting long, save before compression wipes state. Don't wait for the crunch.
10. **Operational docs are living documents.** HEALTHCHECK_SCHEDULE, ALERT_REGISTRY, ISSUE_ESCALATION_PLAYBOOK update whenever the system changes. They're not write-once.

---

## FILES THIS SKILL READS

**Phase 0-1 (Orientation)**:
- `CLAUDE.md`
- `docs/START_HERE.md`
- `tracking/OATHSCORE_SESSION.md`
- `tracking/PROJECT_TRACKER.md`
- `tracking/OWNER_NOTES.md`
- `docs/HEALTHCHECK_SCHEDULE.md`
- `docs/ALERT_REGISTRY.md`
- `docs/ISSUE_ESCALATION_PLAYBOOK.md`

**Phase 2 (Verification)**:
- `src/monitor/config.py` — env var names
- `src/monitor/scheduler.py` — probe wiring
- `src/monitor/alerts.py` — alert thresholds
- `src/monitor/alert_sender.py` — Telegram config
- `src/monitor/incident_tracker.py` — incident files
- `src/monitor/scoring.py` — weights, components
- `src/config.py` — base URLs
- `src/mcp_server.py` — BASE_URL
- `src/events.py` — calendar dates
- `tests/test_api.py` — test URLs
- `.github/workflows/health-check.yml` — CI URLs
- `public/llms.txt`, `public/llms-full.txt`

**Phase 6 (Save)**:
- `src/rate_limit.py` — tier limits (spot check)
- All files in project (inventory)

## FILES THIS SKILL MAY MODIFY

- `tracking/OATHSCORE_SESSION.md` — session state (always)
- `tracking/PROJECT_TRACKER.md` — task status (if changed)
- `tracking/OWNER_NOTES.md` — GitHub issue sync
- `docs/HEALTHCHECK_SCHEDULE.md` — if probes/intervals changed
- `docs/ALERT_REGISTRY.md` — if alerts added/modified
- `docs/ISSUE_ESCALATION_PLAYBOOK.md` — if new failure scenarios
