# OathScore Session State

**Last Updated**: 2026-04-10
**Project**: OathScore — Independent quality ratings for financial data APIs
**Repo**: https://github.com/moxiespirit/oathscore
**Live API**: https://api.oathscore.dev
**Status**: LIVE, accepting real payments

---

## Current Task

Health review and monitoring cleanup (2026-04-10). Removed curistat from monitoring (platform being reworked). Fixed `/alerts` 500 error. Diagnosed 4 APIs at 0% uptime. Created standalone `curistat-mcp` repo for Glama/awesome-mcp-servers compliance. Added OathScore section to Curistat Windmill migration plan.

## What We're Doing

OathScore is two products: (1) `/now` endpoint = world state for trading agents in one call, (2) quality ratings (0-100) for 10 financial data APIs. Built as FastAPI on Railway, with MCP server, Stripe billing, x402 micropayments. Monitoring probes will migrate to Windmill on Hetzner VPS alongside Curistat pipeline.

---

## Cumulative State (what exists NOW)

### Architecture
- **API Server**: FastAPI on Railway ($5/mo), Python 3.12, Docker
- **Background tasks**: asynccontextmanager lifespan, background refresh every 60s
- **Storage**: Dual-write (local JSON + Supabase REST API). Local JSON is ephemeral on Railway.
- **Billing**: Stripe (live mode, real money), webhook with signature verification
- **Micropayments**: x402 protocol (USDC via base network, not yet activated -- needs wallet)
- **MCP Server**: 8 tools, `python -m oathscore_mcp`
- **Domain**: api.oathscore.dev (custom domain on Railway)
- **Standalone curistat-mcp repo**: https://github.com/moxiespirit/curistat-mcp (created 2026-04-10)

### Monitored APIs (10, was 11 -- curistat removed 2026-04-10)
alphavantage, polygon, finnhub, twelvedata, eodhd, fmp, fred, coingecko, alpaca, yfinance

### Known Issues (as of 2026-04-10)
- **finnhub**: 0% uptime (key set but API returning errors -- check if expired)
- **fmp**: 0% uptime (key set but API returning errors -- check if expired)
- **alpaca**: 0% uptime (verify ALPACA_KEY + ALPACA_SECRET set in Railway)
- **eodhd**: 45.5% uptime (intermittent, possibly rate-limited)
- **Low ping counts** (~34 instead of ~43,000): Railway ephemeral FS wipes data on deploy. Structural issue -- Windmill migration will fix.
- **Polygon**: 93.9% uptime but 3.2s avg latency (slow)

### MCP Directory Status
- **Glama (OathScore)**: APPROVED and listed
- **Glama (curistat-mcp)**: Submitted 2026-04-10, pending review
- **awesome-mcp-servers (OathScore PR #2694)**: MERGED
- **awesome-mcp-servers (curistat-mcp PR #2326)**: Updated with new repo URL + Glama badge, waiting on Glama approval
- **mcp.so**: Submitted, waiting
- **mcpservers.org**: Submitted, waiting
- **punkpeye Discord flair**: Optional, offered on PR #2694

### Pricing Tiers
| Tier | /now | /score | Price |
|------|------|--------|-------|
| Free | 10/day | 5/day | $0 |
| Founding (first 50) | 5,000/day | 2,500/day | $9/mo lifetime |
| Pro | 10,000/day | 5,000/day | $29/mo |
| Enterprise | 100,000/day | 50,000/day | $99/mo |

---

## Last Session Changes (2026-04-10)

- Removed curistat from MONITORED_APIS, accuracy probe, and MCP tool descriptions (b7ee7d8)
- Fixed `/alerts` route: severity check used `"high"` instead of `"URGENT"/"CRITICAL"`, added error handling
- Created standalone repo `moxiespirit/curistat-mcp` with full package structure (09f0843, 158db14)
- Submitted curistat-mcp to Glama, updated awesome-mcp-servers PR #2326
- Added OathScore section to Curistat Windmill migration plan (`MYCLONE/docs/WINDMILL_MIGRATION_PLAN.md`)

---

## Active Files

- `src/monitor/config.py` -- monitored API definitions (10 APIs)
- `src/main.py` -- all FastAPI routes
- `src/monitor/ping_probe.py` -- uptime/latency probe
- `src/monitor/alerts.py` -- degradation detection
- `src/monitor/scoring.py` -- composite score computation
- `tracking/PROJECT_TRACKER.md` -- task list (needs update)
- `MYCLONE/docs/WINDMILL_MIGRATION_PLAN.md` -- migration plan with OathScore section

---

## Decisions Made

1. **Free tier tightened** -- 10/day /now, 5/day /score (was unlimited). Drives upgrades.
2. **Founding tier** -- $9/mo lifetime for first 50 subscribers. Creates urgency.
3. **x402 over traditional billing for agents** -- agents can pay per request without signup.
4. **Skip Product Hunt** -- not a fit for B2D/agent tooling.
5. **Skip Reddit** -- no karma, focus on HN + DEV.to + directories.
6. **Stripe under Curistat LLC** -- single legal entity for both products.
7. **Dual-write storage** -- local JSON (fast) + Supabase (persistent). Resilient.
8. **curistat-mcp needs own repo** -- Glama and awesome-mcp-servers require dedicated repos, not subdirectories (2026-04-10)
9. **Remove curistat from OathScore monitoring** -- platform being reworked, no point monitoring during changes (2026-04-10)
10. **Windmill migration covers OathScore** -- same Hetzner VPS, same Windmill instance, zero additional cost. Probes become scheduled scripts. (2026-04-10)

---

## Owner Instructions

### Active Rules
1. Revenue is priority -- "no revenue won't work. the goal is to produce income asap"
2. Keep it simple -- "besides stripe what else is needed for us to just be live. a lot of this is extra"
3. Sponsored comparisons + monthly report = Month 1, not launch
4. No Twitter account for now
5. Owner prefers step-by-step guidance for external platform navigation (Stripe, Glama, etc.)

### Historical Context
- Owner created Stripe account under "Founding Member" name initially, renamed to OathScore
- Reddit account (laguia5) has zero karma -- all subreddits auto-remove posts
- curistat-mcp was a subdirectory of MyClone, rejected by Glama. Extracted to own repo 2026-04-10.

---

## Pending Tasks

**Full task list: `tracking/PROJECT_TRACKER.md`** (needs update -- last touched 2026-03-04)

**Next up (from Priority Queue):**
1. Investigate failing API keys (finnhub, fmp, alpaca) -- may be expired or misconfigured
2. Deploy latest fixes to Railway (`railway up`)
3. First traffic analysis report (was due after 2026-03-20 -- overdue)
4. Windmill migration (probes move to Hetzner VPS alongside Curistat)
5. 3.9 -- Sponsored comparisons -- MONTH 1

**Parked (see `memory/oathscore_pending.md`):**
- Glama approval for curistat-mcp (submitted, pending)
- awesome-mcp-servers PR #2326 (waiting on Glama)
- MCP Discord server-author flair (optional)
- Windmill migration + Hetzner VPS provisioning

---

## Session Log

| Date | Session | Key Actions |
|------|---------|-------------|
| 2026-04-10 | S5 | Health review: removed curistat from monitoring (b7ee7d8), fixed /alerts 500, diagnosed 4 APIs at 0%. Created standalone curistat-mcp repo. Updated awesome-mcp-servers PR #2326. Added OathScore to Windmill migration plan. |
| 2026-03-13 | S4 | AI bot defense hardening: robots.txt 22->55 blocked crawlers, main.py 21->46 UA patterns, honeypot middleware (4 paths), TDM-Reservation header, tdmrep.json route, Cloudflare config. |
| 2026-03-05 | S3 | Alert system (alert_sender.py, incident_tracker.py). Operational docs. Telegram alerts wired. |
| 2026-03-04 | S2 | Supabase integration. API keys for all 6 providers. MCP directory submissions (4). Stripe billing (live). x402 micropayments. Launch posts (HN + DEV.to). Example agents (4). |
| 2026-03-03 | S1 | Built entire product from scratch: Phase 0 (API), Phase 1 (monitoring), Phase 2 (scoring). Deployed to Railway. Custom domain. 17 tests passing. |

---

## Next Action

**Do**: Investigate why finnhub, fmp, and alpaca are returning 0% uptime -- check Railway env vars for FINNHUB_KEY, FMP_KEY, ALPACA_KEY, ALPACA_SECRET. Test each API endpoint manually with the key to confirm validity. Then deploy b7ee7d8 to Railway.
**Done when**: All monitored APIs with valid keys show >0% uptime after a deploy cycle. `/alerts` returns 200 instead of 500.
**Prerequisite**: Access to Railway dashboard to verify env vars, or `railway variables` CLI.
