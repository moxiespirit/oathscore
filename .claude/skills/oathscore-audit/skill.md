# OathScore Deep Audit — Comprehensive Forensic Verification

A full, exhaustive audit of the entire OathScore codebase, infrastructure, and documentation. Reads EVERY source file, traces EVERY relationship, verifies EVERY cross-reference. Leaves no stone unturned.

**This is NOT the session startup skill.** The session skill runs a quick audit. This skill does a COMPLETE forensic sweep — the kind that found 10 bugs in a single session when first run against OathScore. It takes time. It reads everything. It trusts nothing.

## Invocation

```
/oathscore-audit
```

Run when:
- Major changes have been made and you need full verification
- Before any deployment
- When something seems wrong but you can't pinpoint it
- Periodically (weekly) as a health check
- Owner requests a deep audit

## PHILOSOPHY

The audit that found 10 real bugs followed one principle: **read the actual code, compare it against everything else, and prove correctness rather than assume it.**

Every check in this skill follows the pattern:
1. Read source file A
2. Read source file B (or config, or docs, or API response)
3. Verify they agree
4. If they don't → BUG

**Do NOT:**
- Trust the session file's description of what code does
- Assume env vars are correct because they were correct last time
- Skip a check because "it probably hasn't changed"
- Stop after finding the first bug — there are always more

**DO:**
- Read every file listed in every section
- Print findings as you go (so owner sees progress)
- Track EVERY discrepancy, no matter how small
- Categorize by severity: CRITICAL (breaks functionality), MEDIUM (wrong but functional), LOW (cosmetic/docs)

---

## LAYER 1: SOURCE CODE INTEGRITY (every .py file)

### 1.1 Complete Python File Inventory

```bash
find . -type f -name "*.py" -not -path "./.git/*" -not -path "./data/*" -not -name "*.pyc" -not -path "./__pycache__/*" | sort
```

For EACH .py file found:
- Read it
- Note its purpose (1 line)
- Note its imports
- Note what it exports (functions, classes, constants)
- Check: is it referenced by any other file? (orphan check)

### 1.2 Import Chain Verification

For every `from src.X import Y` or `import src.X` in the codebase:
- Does the imported module exist?
- Does the imported name exist in that module?
- Is the import used? (check for dead imports)

```bash
# Extract all internal imports
grep -rn "from src\." --include="*.py" . | grep -v __pycache__
grep -rn "import src\." --include="*.py" . | grep -v __pycache__
```

Flag: broken imports, circular imports, dead imports.

### 1.3 Route Handler Audit

Read `src/main.py` completely. For EVERY `@app.get`, `@app.post`, `@app.middleware`:
- What route does it handle?
- What does it return?
- What can go wrong? (uncaught exceptions, missing error handling)
- Does it have rate limiting applied?
- Does it check authentication where needed?

Build a complete route table:
```
ROUTE TABLE
===========
GET  /now              → aggregator.build_now_response()    [free, rate-limited]
GET  /health           → inline                             [free, no limit]
GET  /score/{api}      → scoring.compute_score()            [free, rate-limited]
... (every route)
```

Cross-reference against:
- `public/llms.txt` endpoint list
- `public/llms-full.txt` endpoint list
- `src/mcp_server.py` tool definitions
- `tests/test_api.py` test coverage

Flag: routes not in docs, routes not tested, routes not in MCP server.

### 1.4 Middleware Chain Audit

Read `src/main.py` middleware stack:
- What order do middlewares execute?
- Does kill switch middleware cover all routes except /health?
- Does rate limiting apply to the right routes?
- Does CORS allow the right origins?
- Are there any middleware conflicts?

### 1.5 Error Handling Audit

For every route handler and background task:
- What happens on exception?
- Is the error logged?
- Does it return a proper error response?
- Can it crash the whole server? (unhandled exception in middleware or startup)

---

## LAYER 2: CONFIGURATION & ENVIRONMENT

### 2.1 Environment Variable Complete Map

Read EVERY source file that accesses `os.environ` or `os.getenv`:
```bash
grep -rn "os\.environ\|os\.getenv\|environ\[" --include="*.py" . | grep -v __pycache__
```

Build a complete table:
```
ENV VAR MAP
===========
Variable Name          | Read By                    | Required? | Railway Set?
SUPABASE_URL           | src/monitor/supabase_store | Yes       | ?
SUPABASE_ANON_KEY      | src/monitor/supabase_store | Yes       | ?
STRIPE_SECRET_KEY      | src/billing.py             | Yes       | ?
... (every env var)
```

Then verify against Railway:
```bash
railway variables 2>/dev/null
```

Flag: any env var read by code but not set in Railway, any Railway var not read by code.

### 2.2 API Key Cross-Reference (Deep)

Read `src/monitor/config.py` MONITORED_APIS dictionary completely.

For EACH monitored API:
- `key_env` value → does this env var exist in Railway?
- `secret_env` value (if present) → does this env var exist in Railway?
- `base_url` → is it the correct production URL? (not staging, not deprecated)
- `health` endpoint → does it actually return 200?
- Each endpoint in `endpoints[]`:
  - Is the path correct?
  - Are the params correct?
  - Are headers handled? (for Alpaca, yfinance)
  - Does `{key}` substitution work?
  - Does `{secret}` substitution work?

Verify by actually calling each API's health/first endpoint:
```bash
# For each API, test the actual endpoint
curl -s --max-time 10 "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
curl -s --max-time 10 "https://query1.finance.yahoo.com/v8/finance/chart/SPY?range=1d&interval=1d" -H "User-Agent: OathScore/1.0"
# ... etc for each API
```

Flag: wrong URLs, missing keys, broken endpoints, auth that doesn't work.

### 2.3 Probe Code vs Config Alignment

Read ALL probe files:
- `src/monitor/ping_probe.py`
- `src/monitor/freshness_probe.py`
- `src/monitor/schema_probe.py`
- `src/monitor/accuracy_probe.py`
- `src/monitor/docs_probe.py`

For EACH probe, verify:
- Does it handle the `headers` dict from endpoint config? (needed for Alpaca, yfinance)
- Does it handle `{key}` substitution in both params AND headers?
- Does it handle `{secret}` substitution?
- Does it skip endpoints correctly when keys are missing?
- Does it import `get_api_secret` where needed?
- Does it store results correctly? (what function does it call in store.py?)

Flag: probes that can't handle new API patterns, probes not storing results.

### 2.4 Scoring Engine Deep Dive

Read `src/monitor/scoring.py` line by line.

For EACH of the 7 scoring components (accuracy, uptime, freshness, latency, schema, docs, trust):
- HOW is it computed? (trace the exact logic)
- WHAT data does it read? (which JSON file?)
- WHAT happens when data is missing? (does it return None? 0? default?)
- Is the weight correct? (compare against METHODOLOGY.md)
- Are the brackets/thresholds reasonable?

Verify the reweighting logic:
- When a component is None, do the remaining weights sum to 1.0?
- Can a score ever exceed 100 or go below 0?
- Does the grade calculation match the thresholds?

Verify `persist_daily_scores()`:
- What fields does it write to Supabase?
- Do those fields match the `daily_scores` table schema in migrations?
- Is it called by the scheduler? At what interval?

### 2.5 Scheduler Complete Wiring Check

Read `src/monitor/scheduler.py` completely.

Build a table:
```
SCHEDULER WIRING
================
Task Name      | Function              | Interval  | Import Source
ping           | ping_all              | 60s       | src.monitor.ping_probe
freshness      | check_freshness       | 300s      | src.monitor.freshness_probe
schema         | check_schemas         | 3600s     | src.monitor.schema_probe
... (every task)
```

Cross-reference:
- Every probe file → is it wired in the scheduler?
- Every scheduler task → does the imported function exist?
- Are intervals reasonable?
- What happens if a task throws an exception? (does it crash the loop?)

### 2.6 Storage Layer Verification

Read `src/monitor/store.py` completely.
Read `src/monitor/supabase_store.py` completely.

For EACH store function:
- Does it write to local JSON AND Supabase (dual-write)?
- What file path does it write locally?
- What Supabase table does it write to?
- Does the data shape match the migration schema?
- Is there error handling if Supabase is down?

Read `migrations/001_initial.sql`:
- List every table and column
- Cross-reference against store.py write calls
- Cross-reference against supabase_store.py

Flag: tables that exist but nothing writes to them, store calls that write to non-existent tables.

---

## LAYER 3: BILLING & SECURITY

### 3.1 Stripe Integration Audit

Read `src/billing.py` completely.

- What Stripe API calls does it make?
- How are API keys generated? (format, storage)
- How is the webhook verified? (HMAC signature check)
- What happens on subscription creation/cancellation?
- Are there any hardcoded Stripe IDs that could go stale?
- Does the pricing match what's in llms.txt and the pricing endpoint?

Read `src/rate_limit.py` completely.

- What are the tier limits? (requests per day for each tier)
- How is the tier determined? (API key → Stripe lookup → tier)
- What happens when rate limit is hit? (429 response?)
- Is the rate limiter per-IP for free tier?

### 3.2 Kill Switch Verification

Read the kill switch implementation in `src/main.py`:
- Where is the kill switch file? (`data/kill_switch.json`)
- What routes does it exempt? (should be /health only)
- What status code does it return? (should be 503)
- Can the kill switch be activated remotely? (should be file-based only)
- Does /health show kill switch status?

### 3.3 x402 Micropayment Verification

Read `src/x402.py` (if exists):
- Is it active or dormant?
- What wallet address is configured?
- What are the per-call prices?
- Is it wired into the middleware chain?

### 3.4 Security File Verification

Read `public/robots.txt`:
- Are training crawlers blocked?
- Are discovery bots allowed?
- Any new crawlers that should be added?

Read `public/.well-known/security.txt`:
- Is the Expires date still in the future?
- Is the contact information correct?

Read `public/.well-known/ai-plugin.json`:
- Is the schema version current?
- Are URLs correct?
- Is the description accurate?

---

## LAYER 4: DOCUMENTATION & PUBLIC FILES

### 4.1 llms.txt Accuracy

Read `public/llms.txt`. For EVERY claim:
- Endpoint list → does each endpoint exist in main.py routes?
- Rate limits → do they match rate_limit.py?
- Pricing → does it match billing.py?
- MCP tool count → does it match mcp_server.py?
- Base URL → correct?

### 4.2 llms-full.txt Accuracy

Read `public/llms-full.txt`. Same checks as 4.1, plus:
- Response field descriptions → do they match actual API responses?
- Rated APIs table → does it match MONITORED_APIS in config.py?
- Scoring methodology → does it match scoring.py weights?
- Contact/GitHub URLs → correct?

### 4.3 ai.txt Accuracy

Read `public/ai.txt`:
- All URLs correct and reachable?

### 4.4 README.md Accuracy

Read `README.md`:
- API count matches MONITORED_APIS?
- Endpoint examples use correct URLs?
- MCP config is correct?
- Scoring methodology matches scoring.py?
- Installation instructions work?

### 4.5 CLAUDE.md Accuracy

Read `CLAUDE.md`:
- Directory map matches actual directory structure?
- Env var names match code?
- Deploy instructions correct?

### 4.6 Session File Comprehensive Verification

Read `tracking/OATHSCORE_SESSION.md`:
- File map: EVERY file listed → does it exist on disk?
- File map: ANY file on disk not in the map?
- Constants section: EVERY constant → matches actual code?
- Env var table: EVERY entry → matches config.py key_env AND Railway?
- Known bugs: any resolved but not marked?
- Pending tasks: any completed but not moved?

### 4.7 Project Tracker Sync

Read `tracking/PROJECT_TRACKER.md`:
- Tasks marked DONE → are they actually done? (check files exist, features work)
- Tasks marked TODO → are any already done? (check recent commits)
- Priority queue → still accurate?
- Status summary counts → match the actual task statuses?

---

## LAYER 5: EXTERNAL INTEGRATIONS

### 5.1 Live API Comprehensive Test

Test EVERY public endpoint:

```bash
# Core endpoints
curl -s --max-time 10 https://api.oathscore.dev/health | python -m json.tool
curl -s --max-time 10 https://api.oathscore.dev/now | python -c "import sys,json; d=json.load(sys.stdin); print(json.dumps({k:type(v).__name__ for k,v in d.items()}, indent=2))"
curl -s --max-time 10 https://api.oathscore.dev/scores | python -m json.tool
curl -s --max-time 10 https://api.oathscore.dev/pricing | python -m json.tool

# Score endpoints for each monitored API
for api in curistat alphavantage polygon finnhub twelvedata eodhd fmp fred coingecko alpaca yfinance; do
  echo "=== $api ==="
  curl -s --max-time 10 "https://api.oathscore.dev/score/$api" | python -c "import sys,json; d=json.load(sys.stdin); print(f'score={d.get(\"composite_score\",\"N/A\")} grade={d.get(\"grade\",\"N/A\")} points={d.get(\"data_points\",0)}')" 2>/dev/null
done

# Compare endpoint
curl -s --max-time 10 "https://api.oathscore.dev/compare?apis=polygon,finnhub" | python -m json.tool

# Alerts endpoint
curl -s --max-time 10 https://api.oathscore.dev/alerts | python -m json.tool

# Status endpoint
curl -s --max-time 10 https://api.oathscore.dev/status | python -c "import sys,json; d=json.load(sys.stdin); print(f'uptime probes: {d.get(\"probe_intervals\",{})}')" 2>/dev/null

# Discovery files
curl -s --max-time 10 https://api.oathscore.dev/llms.txt | head -5
curl -s --max-time 10 https://api.oathscore.dev/llms-full.txt | head -5
curl -s --max-time 10 https://api.oathscore.dev/.well-known/ai-plugin.json | python -m json.tool
curl -s --max-time 10 https://api.oathscore.dev/.well-known/security.txt
curl -s --max-time 10 https://api.oathscore.dev/robots.txt | head -10
```

For EACH response, verify:
- Status code is 200 (or expected code)
- Response body has expected structure
- Data makes sense (VIX not 0, exchanges have reasonable status)
- Rate limit headers present where expected

### 5.2 Monitored API Reachability

For EACH API in MONITORED_APIS, test one endpoint:
```bash
# Test each monitored API is actually reachable
curl -s --max-time 10 -o /dev/null -w "%{http_code}" "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
curl -s --max-time 10 -o /dev/null -w "%{http_code}" "https://query1.finance.yahoo.com/v8/finance/chart/SPY?range=1d&interval=1d" -H "User-Agent: OathScore/1.0"
curl -s --max-time 10 -o /dev/null -w "%{http_code}" "https://api.stlouisfed.org/fred/series/observations?series_id=DGS10&limit=1&sort_order=desc&file_type=json&api_key=FRED_KEY_HERE"
# ... etc
```

Flag: any monitored API returning non-200.

### 5.3 GitHub Repository Sync

```bash
# Check remote vs local
cd <project_root> && git fetch origin 2>/dev/null
git log --oneline origin/main..HEAD  # local ahead
git log --oneline HEAD..origin/main  # remote ahead

# Uncommitted changes
git status -s

# Untracked files that should be committed
git status -s | grep "^??" | grep -v "__pycache__\|.pyc\|data/\|.env"
```

Flag: uncommitted changes, untracked source files, local/remote divergence.

### 5.4 MCP Directory Status

```bash
# Glama
curl -s "https://glama.ai/mcp/servers/oathscore" -o /dev/null -w "%{http_code}" 2>/dev/null

# GitHub PRs and issues
gh issue view 668 --repo chatmcp/mcpso --json state,title 2>/dev/null || echo "Cannot check mcp.so"
gh pr view 2694 --repo punkpeye/awesome-mcp-servers --json state,title 2>/dev/null || echo "Cannot check punkpeye PR"
```

### 5.5 Stripe Health

```bash
curl -s --max-time 10 https://api.oathscore.dev/pricing | python -c "
import sys,json; d=json.load(sys.stdin)
tiers=d.get('tiers',{})
for name,tier in tiers.items():
    print(f'{name}: \${tier.get(\"price_monthly\",\"?\")}/mo, {tier.get(\"slots_remaining\",\"?\")} slots')
" 2>/dev/null || echo "Pricing endpoint failed"
```

### 5.6 Railway Deployment Health

```bash
# Check Railway variables count
railway variables 2>/dev/null | wc -l || echo "Railway CLI not available"

# Check Railway logs for errors
railway logs --limit 50 2>/dev/null | grep -iE "error|exception|traceback|critical" | head -10 || echo "Railway CLI not available"
```

---

## LAYER 6: DEPENDENCY & INFRASTRUCTURE

### 6.1 Requirements.txt Audit

Read `requirements.txt`:
- For EACH dependency: is it actually imported somewhere in the code?
- For EACH import in the code: is the package in requirements.txt?
- Are there version pins? Are any outdated?

```bash
# Cross-reference
cat requirements.txt
grep -rn "^import \|^from " --include="*.py" . | grep -v __pycache__ | awk '{print $2}' | sort -u
```

### 6.2 Dockerfile Audit

Read `Dockerfile`:
- Base image reasonable?
- Does it copy all necessary files?
- Does it expose the right port?
- Does it install all requirements?
- Any security concerns? (running as root, exposing secrets)

Read `.dockerignore`:
- Are data files excluded?
- Are .env files excluded?
- Are .git files excluded?

### 6.3 GitHub Actions Audit

Read `.github/workflows/health-check.yml`:
- All URLs correct (api.oathscore.dev, not old Railway URL)?
- Schedule reasonable?
- Does it actually test what it claims to?

### 6.4 Railway Config

Read `railway.json` (if exists):
- Build command correct?
- Start command correct?
- Region set?

---

## FINAL REPORT

After ALL layers complete, produce the full audit report:

```
╔══════════════════════════════════════════════════════════════╗
║              OATHSCORE DEEP AUDIT REPORT                     ║
║              Date: [DATE]                                    ║
╚══════════════════════════════════════════════════════════════╝

LAYER 1: SOURCE CODE INTEGRITY
  Python files found:        N
  Import chains verified:    N OK / N broken
  Routes documented:         N/N
  Routes tested:             N/N
  Dead imports:              N
  Orphan files:              N

LAYER 2: CONFIGURATION & ENVIRONMENT
  Env vars (code vs Railway): N matched / N mismatched
  Monitored APIs:            N configured / N with keys / N reachable
  Probe-config alignment:    N OK / N issues
  Scoring components:        N active / N placeholder
  Scheduler tasks:           N wired / N missing
  Storage dual-write:        N OK / N single-write only

LAYER 3: BILLING & SECURITY
  Stripe integration:        [OK / issues]
  Rate limiting:             [OK / issues]
  Kill switch:               [OK / issues]
  x402:                      [Active / Dormant]
  Security files:            N/N present and current

LAYER 4: DOCUMENTATION
  llms.txt accuracy:         N/N claims verified
  llms-full.txt accuracy:    N/N claims verified
  README accuracy:           N/N claims verified
  CLAUDE.md accuracy:        N/N claims verified
  Session file accuracy:     N/N entries verified
  Tracker sync:              N/N tasks correctly statused

LAYER 5: EXTERNAL INTEGRATIONS
  Live API endpoints:        N/N responding
  Monitored APIs reachable:  N/N
  GitHub sync:               [Clean / N uncommitted / N diverged]
  MCP directories:           [status of each]
  Stripe:                    [OK / issue]
  Railway:                   [OK / N errors in logs]

LAYER 6: INFRASTRUCTURE
  Dependencies:              N in requirements / N imported / N unused / N missing
  Dockerfile:                [OK / issues]
  CI/CD:                     [OK / issues]

═══════════════════════════════════════════════════════════════

BUGS FOUND: N
──────────────────────────────────────────────────────────────
[CRITICAL] Bug description — file:line — impact
[CRITICAL] Bug description — file:line — impact
[MEDIUM]   Bug description — file:line — impact
[LOW]      Bug description — file:line — impact

STALE DOCUMENTATION: N entries
──────────────────────────────────────────────────────────────
[File] — what's stale — current value vs documented value

RECOMMENDATIONS:
──────────────────────────────────────────────────────────────
1. [Fix critical bugs immediately]
2. [Update stale docs]
3. [Address medium bugs]
4. [Infrastructure improvements]

═══════════════════════════════════════════════════════════════
Audit complete. N files read. N cross-references checked.
```

---

## CRITICAL RULES FOR THIS SKILL

1. **READ EVERY FILE.** Not "check if it exists." Open it. Read the contents. Verify the logic.
2. **TRUST NOTHING.** The session file, the docs, the README — they are claims to verify, not facts to accept.
3. **CROSS-REFERENCE EVERYTHING.** The bug pattern is always: File A says X, File B says Y, X ≠ Y.
4. **DON'T STOP AT THE FIRST BUG.** There are always more. The first 3 times this audit was attempted, it stopped too early. Go through EVERY layer.
5. **PRINT PROGRESS.** The owner should see each layer completing in real time, not wait 10 minutes for a silent result.
6. **SEVERITY MATTERS.** CRITICAL = breaks functionality for users. MEDIUM = wrong but works. LOW = cosmetic or docs-only.
7. **NO SHORTCUTS.** If a layer says "read every .py file," read every .py file. If it says "test every endpoint," test every endpoint. The bugs hide in the files you skip.
8. **INCLUDE LINE NUMBERS.** When reporting bugs, include the exact file path and line number so fixes are immediate.
9. **VERIFY FIXES.** If you fix a bug during the audit, re-run that specific check to prove the fix worked.
10. **UPDATE SESSION FILE.** After the audit, update tracking/OATHSCORE_SESSION.md with any bugs found, fixed, or remaining.
