# OathScore Session — Startup, Deep Audit & Shutdown Skill

Session startup and shutdown for the OathScore project. Loads live session state, runs a deep code+infra audit that catches real bugs, verifies all services, presents a briefing. Auto-saves on shutdown.

## Invocation

```
/oathscore-session
```

Run at the start of any OathScore work session, or when wrapping up.

---

## PHASE 1: LOAD LIVE STATE

Read these files IN ORDER before doing anything:

### 1.0 Project Rules (MANDATORY FIRST)
```
Read CLAUDE.md
```
Re-read the project's CLAUDE.md rules. Internalize any constraints, conventions, or instructions before proceeding. If CLAUDE.md has changed since last session, note the changes in the briefing.

### 1.1 Session State (WHERE WE LEFT OFF)
```
Read tracking/OATHSCORE_SESSION.md
```
This is the SINGLE SOURCE OF TRUTH for project state. Contains:
- Current task & what we're doing
- Cumulative state (architecture, endpoints, tools, probes, pricing)
- Complete file map (every file with purpose)
- All credentials & env vars
- External services (Railway, Stripe, Supabase, GitHub)
- Monitored APIs & MCP directory status
- Marketing status
- Completed & pending tasks
- Decisions made
- Owner instructions (Active Rules)
- Build timeline & session log

### 1.2 Project Tracker (WHAT NEEDS DOING)
```
Read tracking/PROJECT_TRACKER.md
```
This is the master task list organized by initiative. Contains:
- All tasks with status (DONE/TODO/WAITING/IN PROGRESS)
- Priority queue (what to do next)
- Status summary counts
- AI safety phases (A/B/C by urgency)

### 1.3 Recent Git Activity
```bash
cd <project_root> && git log --oneline --stat -20
```

### 1.4 Uncommitted Changes
```bash
cd <project_root> && git status -s
```

### 1.5 Staleness Detection
Check the "Last Updated" date in `tracking/OATHSCORE_SESSION.md`.
- If updated today: NORMAL MODE (lighter audit)
- If updated yesterday or earlier: **FULL RECONSTRUCTION MODE** (docs may be stale, audit everything)

Print which mode is active:
```
AUDIT MODE: [NORMAL / FULL RECONSTRUCTION (docs last updated: DATE)]
```

---

## PHASE 2: DEEP CODE & INFRASTRUCTURE AUDIT

**This is the critical phase that catches real bugs.** Do NOT skip it. Read actual source files and cross-reference them against the session doc, each other, and the live API.

### 2.1 Cross-Reference: Env Var Names

Read `src/monitor/config.py` and extract every `key_env` value. Then compare against the "Railway Environment Variables" table in the session file.

```
For each API in MONITORED_APIS:
  - What does code read? (key_env value)
  - What is set in Railway? (session file table)
  - MATCH or MISMATCH?
```

**ANY MISMATCH = CRITICAL BUG** (probes run unauthenticated). Flag immediately.

### 2.2 Cross-Reference: URLs

Read these files and extract all hardcoded URLs:
- `src/config.py` — BASE_URL, CURISTAT_API_URL
- `src/mcp_server.py` — BASE_URL default
- `tests/test_api.py` — BASE constant
- `.github/workflows/health-check.yml` — all curl URLs
- `public/llms.txt` — all URLs
- `public/llms-full.txt` — all URLs

**ALL should point to `https://api.oathscore.dev`** (not the old Railway URL `oathscore-production.up.railway.app`).

Flag any stale URLs.

### 2.3 Cross-Reference: Scoring Engine vs Methodology

Read `src/monitor/scoring.py` and verify:
- Are ALL 7 weight components actually computed (not None/placeholder/hardcoded)?
  - accuracy: computed from forecast_snapshots? Or None (acceptable if <30 days)?
  - uptime: from ping data?
  - freshness: from freshness.json (NOT None)?
  - latency: from ping latency_ms?
  - schema: from schema checks?
  - docs: from docs_checks?
  - trust: computed from real signals (NOT hardcoded)?
- Does the reweighting logic work correctly when components are missing?
- Are the latency brackets and letter grade thresholds reasonable?

Flag any component returning None/placeholder/hardcoded value.

### 2.4 Cross-Reference: Scheduler vs Probes

Read `src/monitor/scheduler.py` and verify every probe listed in the session file is actually wired:
- ping_probe → ping_all
- freshness_probe → check_freshness
- schema_probe → check_schemas
- accuracy_probe → snapshot_forecasts + verify_forecasts
- docs_probe → check_docs
- scoring → persist_daily_scores (writes to Supabase daily)

Flag any probe that exists as a file but isn't in the scheduler, or vice versa.

### 2.5 Cross-Reference: Example Agents vs API Contract

Read ALL files in `examples/`:
- Do they use the correct API response field names? (e.g., `status == "open"` not `is_open`)
- Do they use the correct BASE_URL?
- Do they handle error cases?

Flag any example using fields that don't exist in the actual API response.

### 2.6 Cross-Reference: Public Discovery Files vs Reality

Read `public/llms.txt` and `public/llms-full.txt`:
- Tool count matches actual MCP tools in `src/mcp_server.py`?
- Rate limits match `src/rate_limit.py` TIER_LIMITS?
- Pricing matches `src/billing.py`?
- Endpoint list matches routes in `src/main.py`?
- Base URL is correct?

Flag any stale content.

### 2.7 Cross-Reference: Events Calendar Expiry

Read `src/events.py`:
- What's the LAST date in FIXED_EVENTS FOMC list?
- What's the LAST date in FIXED_EVENTS CPI list?
- What's the LAST date in SCHEDULED_EVENTS_2026?
- Are there future years covered?

Flag if the calendar will expire within 6 months.

### 2.8 Cross-Reference: Session File Accuracy

Compare the session file's "Key Constants & Configuration" section against actual code:
- Do the constants listed match what's actually in the source?
- Are any new constants missing from the session file?
- Are any listed constants stale (code changed but session file not updated)?

Spot check at least: `src/rate_limit.py` TIER_LIMITS, `src/billing.py` key format, `src/monitor/alerts.py` thresholds.

### 2.9 File Inventory Audit

List ALL files in the project:
```bash
find . -type f -not -path './.git/*' -not -path './data/*' -not -path './.claude/*' -not -path './node_modules/*' -not -name '*.pyc' | sort
```

Compare against the File Map in the session file. Flag:
- Files on disk but NOT in the file map (undocumented)
- Files in the file map but NOT on disk (deleted but still listed)

### 2.10 Supabase Table Audit

Read `migrations/001_initial.sql` and compare against the Supabase Tables section in the session file:
- Do all tables listed in the migration exist in the session doc?
- Does the code (`store.py`) write to all tables that exist?
- Is `daily_scores` being written to (via `persist_daily_scores` in scheduler)?

### 2.11 Live API Smoke Test

```bash
# Health
curl -s --max-time 10 https://api.oathscore.dev/health

# /now — check all top-level keys exist
curl -s --max-time 10 https://api.oathscore.dev/now | python -c "
import sys,json
d=json.load(sys.stdin)
required=['timestamp','exchanges','volatility','events','data_health','meta']
missing=[k for k in required if k not in d]
if missing: print(f'MISSING KEYS: {missing}')
else: print(f'OK: VIX={d[\"volatility\"].get(\"vix\",\"N/A\")}, exchanges={len(d[\"exchanges\"])}, events_next={bool(d[\"events\"].get(\"next\"))}')
"

# /scores — check monitored count
curl -s --max-time 10 https://api.oathscore.dev/scores | python -c "
import sys,json; d=json.load(sys.stdin)
print(f'APIs: {len(d.get(\"monitored_apis\",[]))}, scores: {len(d.get(\"scores\",{}))}')
"

# /pricing — check tiers
curl -s --max-time 10 https://api.oathscore.dev/pricing | python -c "
import sys,json; d=json.load(sys.stdin)
print(f'Tiers: {list(d.get(\"tiers\",{}).keys())}')
"
```

### 2.12 MCP Directory Status
```bash
gh issue view 668 --repo chatmcp/mcpso --json state,title 2>/dev/null || echo "Cannot check mcp.so"
gh pr view 2694 --repo punkpeye/awesome-mcp-servers --json state,title 2>/dev/null || echo "Cannot check punkpeye PR"
```

### 2.13 Stripe & Supabase Health
```bash
# Stripe via pricing endpoint
curl -s --max-time 10 https://api.oathscore.dev/pricing | python -c "
import sys,json; d=json.load(sys.stdin)
slots=d.get('tiers',{}).get('founding',{}).get('slots_remaining','?')
print(f'Stripe OK, founding slots: {slots}')
" 2>/dev/null || echo "Stripe check failed"

# Railway logs for Supabase errors
railway logs --limit 20 2>/dev/null | grep -i "supabase\|error" || echo "Railway CLI not available"
```

### Audit Summary

After ALL checks, compile:

```
DEEP AUDIT RESULTS
==================
Env var names:       [MATCH / N MISMATCHES]
URLs:                [ALL CORRECT / N STALE]
Scoring components:  [ALL ACTIVE / N PLACEHOLDER]
Scheduler wiring:    [ALL PROBES CONNECTED / N MISSING]
Example agents:      [ALL CORRECT / N BUGS]
Discovery files:     [ALL CURRENT / N STALE]
Calendar expiry:     [OK through YYYY / EXPIRING SOON]
Session file accuracy: [CURRENT / N STALE ENTRIES]
File inventory:      [COMPLETE / N UNDOCUMENTED, N DELETED]
Supabase tables:     [ALL WRITTEN / N UNUSED]
Live API:            [ALL OK / N FAILURES]
MCP directories:     [status of each]
Stripe:              [OK / issue]
Supabase:            [OK / errors]

BUGS FOUND: N
[List each bug with severity: CRITICAL / MEDIUM / LOW]

STALE SESSION FILE ENTRIES: N
[List each stale entry that needs updating]
```

---

## PHASE 3: PRESENT BRIEFING

After loading state, running audit, and verifying services, present:

```
OATHSCORE SESSION BRIEFING - [DATE]
=====================================

PROJECT: OathScore — Independent quality ratings for financial data APIs
API: https://api.oathscore.dev
REPO: https://github.com/moxiespirit/oathscore

AUDIT MODE: [NORMAL / FULL RECONSTRUCTION]

SERVICES:
  API Health: [OK / DOWN]
  /now endpoint: [VIX=X, N exchanges, events=Y/N]
  Scoring: [N APIs monitored, N with scores]
  Stripe: [OK, N founding slots remaining]
  Supabase: [OK / errors found]

DEEP AUDIT: [ALL CLEAR / N BUGS FOUND]
  [List any bugs found with severity]
  [List any stale session file entries]

MCP DIRECTORIES:
  Glama: [Approved]
  mcp.so: [status]
  awesome-mcp-servers PR: [status]
  mcpservers.org: [status]

MARKETING:
  HN: [posted, check stats]
  DEV.to: [posted, check stats]
  Reddit: [blocked, need karma]

WHERE WE LEFT OFF:
  [Current task from session file]

RECENT GIT ACTIVITY:
  [Last 5 commits with files changed]

UNCOMMITTED CHANGES:
  [List or "clean"]

PENDING TASKS:
  1. [highest priority]
  2. [second priority]
  3. [third priority]

OWNER INSTRUCTIONS (Active):
  [List active rules from session file]

SUBSCRIBERS: [Check Stripe dashboard count]
DAYS UNTIL SCORES PUBLISH: [30 - days since 2026-03-03]

RECOMMENDED ACTIONS:
  1. [Fix any CRITICAL bugs first]
  2. [Update stale session file entries]
  3. [Next pending task]
```

---

## PHASE 4: WAIT FOR OWNER

Do NOT start work autonomously. Present the briefing and wait for direction.

If CRITICAL bugs were found in the audit, highlight them prominently and recommend fixing them first.

---

## AUTO-SAVE (Shutdown / Context Getting Long)

### When to Save
- Owner says goodbye/done/wrap up
- Context getting long (proactively save)
- Major milestone reached
- Switching to different project

### Save Process

#### Step 1: Read existing session file FIRST
```
Read tracking/OATHSCORE_SESSION.md
```
**UPDATE, do not overwrite.** Preserve all cumulative state, credentials, file maps.

#### Step 2: Run mini-audit before saving

Before writing session state, do a quick verification:

**2a. File map accuracy**: List all files on disk, compare to session file File Map. Add any new files, remove deleted ones.

```bash
# Quick file inventory
find . -type f -name "*.py" -not -path './.git/*' -not -path './data/*' -not -name '*.pyc' | sort
find . -type f -name "*.md" -not -path './.git/*' | sort
find . -type f -name "*.txt" -path './public/*' | sort
find . -type f -name "*.json" -path './public/*' -o -name "*.yml" -path './.github/*' | sort
```

**2b. Constants accuracy**: Spot-check 3 key constants against actual code:
- `src/rate_limit.py` — TIER_LIMITS values
- `src/monitor/scoring.py` — WEIGHTS values
- `src/events.py` — last date in FOMC/CPI lists

**2c. Env var table accuracy**: Read `src/monitor/config.py` key_env values, compare to session file env var table.

**2d. Known bugs section**: Are all listed bugs still relevant? Any new ones discovered this session?

#### Step 3: Gather session state (update these sections)

**Current Task**: What was being worked on when session ended. Specific enough for a new session to start immediately.

**What We're Doing**: 1-2 sentences, domain terms.

**Cumulative State**: UPDATE the existing inventory. Add new files, endpoints, services. Remove deprecated items. Keep it an inventory, not a changelog. Reference files for details, keep <50 lines.

**Last Session Changes**: REPLACE the previous session's changes (don't accumulate). Max 5 bullets of what THIS session accomplished.

**File Map**: ADD any new files created this session. Remove any deleted files. Verify completeness via Step 2a.

**Key Constants & Configuration**: UPDATE any constants that changed this session. Verify via Step 2b.

**External Services & Credentials**: UPDATE if any new keys, env vars, or services were added. Verify via Step 2c.

**Known Bugs & Gaps**: UPDATE based on Step 2d. Mark fixed bugs, add new ones.

**Decisions Made**: APPEND new decisions with date/reasoning.

**Owner Instructions**:
- **Active Rules**: Still apply. ADD new ones verbatim.
- **Historical Context**: Move resolved instructions here.
- **Superseded**: REMOVE entirely.

**Completed Tasks**: MOVE newly completed items from Pending to Completed with date.

**Pending Tasks**: ADD new tasks discovered. REMOVE completed ones.

**Session Log**: APPEND one row for this session. Keep last 10 rows.

**Build Timeline**: APPEND new milestones.

**Next Session Startup**: UPDATE the 7-step checklist if anything changed.

#### Step 4: Write updated session file
Use Edit tool to update specific sections, preserving the rest.

#### Step 5: Route learnings
- New credentials/env vars → session file External Services section
- New files → session file File Map
- Bugs found → session file Known Bugs section
- Architecture changes → session file Cumulative State
- Stale entries fixed → note in session log

#### Step 6: Update task list
If using Claude Code task tools, sync task status with session file.

#### Step 7: Confirm save
Print:
```
SESSION SAVED
=============
File: tracking/OATHSCORE_SESSION.md
Updated sections: [list]
New items: [list of new files/credentials/tasks added]
Bugs found/fixed: [count]
Stale entries corrected: [count]
Next action: [specific next step for new session]
```

---

## CRITICAL RULES

1. **Session file is SINGLE SOURCE OF TRUTH** for "where are we." Everything lives there.
2. **Read BEFORE writing** — always load existing state first, then update. Never overwrite.
3. **Credentials go in the session file** — Railway env vars, Stripe keys, Supabase URL, API keys. A new session must be able to find everything without hunting.
4. **File map must be complete** — every file in the project documented with purpose. New files added immediately.
5. **Owner instructions preserved VERBATIM** — exact quotes, not paraphrases.
6. **Prune aggressively** — Cumulative State <50 lines (reference files for details). Last Session Changes = THIS session only. Remove resolved owner instructions.
7. **When providing copy-paste text to owner** — write to a .txt file, not inline. Markdown renders in Claude's output and owner can't copy raw syntax.
8. **AUDIT IS NOT OPTIONAL** — Phase 2 runs every session. It's what catches real bugs (env var mismatches, stale URLs, placeholder scores, missing scheduler wiring). Skipping it means shipping broken code.
9. **Read actual source files** — never trust the session file's description of what code does. Read the code. Compare against docs. That's how bugs #1-10 were found.
10. **Cross-reference everything** — the pattern that catches bugs is: read file A, read file B, check if they agree. Code vs config, code vs docs, code vs API response, code vs session file.

---

## FILES THIS SKILL READS (every session)

**Source code (for audit)**:
- `src/monitor/config.py` — env var names (key_env values)
- `src/monitor/scoring.py` — weights, component computation
- `src/monitor/scheduler.py` — probe wiring
- `src/config.py` — base URLs, constants
- `src/mcp_server.py` — BASE_URL default
- `src/rate_limit.py` — tier limits
- `src/billing.py` — key format, pricing
- `src/events.py` — calendar dates
- `src/monitor/alerts.py` — alert thresholds
- `src/main.py` — routes (for endpoint cross-reference)
- `examples/*.py` — all example agents

**Public files (for audit)**:
- `public/llms.txt` — agent description
- `public/llms-full.txt` — full docs
- `tests/test_api.py` — test URLs
- `.github/workflows/health-check.yml` — CI URLs

**Tracking/docs**:
- `tracking/OATHSCORE_SESSION.md` — session state (primary)
- `tracking/PROJECT_TRACKER.md` — master task list (initiatives, priorities, status)
- `CLAUDE.md` — project rules
- `docs/BUSINESS_CONCEPT.md` — business plan reference
- `docs/IMPLEMENTATION_PLAN.md` — phase plan reference
- `docs/MCP_REGISTRATION.md` — directory submission status
- `docs/launch_posts.md` — marketing post status
- `migrations/001_initial.sql` — Supabase schema

## FILES THIS SKILL MAY MODIFY
- `tracking/OATHSCORE_SESSION.md` — session state updates (always)
- `tracking/PROJECT_TRACKER.md` — task status updates (mark DONE, add new tasks, update priorities)
- `docs/MCP_REGISTRATION.md` — directory status updates
- `docs/launch_posts.md` — marketing status updates
- Any source file where a bug is found (with owner approval)
