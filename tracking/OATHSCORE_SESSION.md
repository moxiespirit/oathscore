# OathScore Session State

**Last Updated**: 2026-03-13
**Project**: OathScore — Independent quality ratings for financial data APIs
**Repo**: https://github.com/moxiespirit/oathscore
**Live API**: https://api.oathscore.dev
**Status**: LIVE, accepting real payments

---

## Current Task

AI bot defense hardening (2026-03-13). Expanded anti-AI-bot protections: 55 blocked crawlers in robots.txt, 46 UA patterns in middleware, honeypot paths, TDM-Reservation header, tdmrep.json for EU AI Act compliance. Cloudflare configured: AI Labyrinth, Bot Fight Mode, per-crawler selective controls.

## What We're Doing

OathScore is two products: (1) `/now` endpoint = world state for trading agents in one call, (2) quality ratings (0-100) for 7 financial data APIs. Built as FastAPI on Railway, with MCP server, Stripe billing, x402 micropayments.

---

## Cumulative State (what exists NOW)

### Architecture
- **API Server**: FastAPI on Railway ($5/mo), Python 3.12, Docker
- **Background tasks**: asynccontextmanager lifespan, background refresh every 60s
- **Storage**: Dual-write (local JSON + Supabase REST API)
- **Billing**: Stripe (live mode, real money), webhook with signature verification
- **Micropayments**: x402 protocol (USDC via base network, not yet activated — needs wallet)
- **MCP Server**: 8 tools, `python -m oathscore_mcp`
- **Domain**: api.oathscore.dev (custom domain on Railway)

### API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Landing/agent entry point |
| `/now` | GET | World state (exchanges, volatility, events, health) |
| `/health` | GET | Service health check |
| `/scores` | GET | All API monitoring scores |
| `/score/{api_name}` | GET | Individual API quality score |
| `/compare?apis=a,b` | GET | Side-by-side API comparison |
| `/alerts` | GET | Active degradation alerts |
| `/status` | GET | Full system status + raw metrics |
| `/pricing` | GET | Current tier pricing |
| `/subscribe` | POST | Create Stripe checkout session |
| `/subscribe/success` | GET | Post-checkout landing |
| `/webhooks/stripe` | POST | Stripe webhook (signature verified) |
| `/llms.txt` | GET | Agent-readable product description |
| `/llms-full.txt` | GET | Complete endpoint documentation |
| `/robots.txt` | GET | Agent-aware robots.txt |
| `/ai.txt` | GET | AI discovery pointer |
| `/.well-known/ai-plugin.json` | GET | ChatGPT plugin manifest |
| `/.well-known/tdmrep.json` | GET | W3C TDMRep declaration (EU AI Act) |
| `/openapi.json` | GET | OpenAPI 3.0.3 spec (auto-generated) |
| `/docs` | GET | Interactive Swagger UI |

### MCP Tools (8)
get_now, get_exchanges, get_volatility, get_events, get_score, compare_apis, get_alerts, check_health

### Monitoring Probes
| Probe | Interval | What it does |
|-------|----------|-------------|
| Ping | 60s | HTTP health check, latency measurement |
| Freshness | 300s (5m) | Check if "real-time" data is actually fresh |
| Schema | 3600s (1h) | Detect breaking changes in API responses |
| Accuracy | 3600s (1h) | Snapshot forecasts for later verification |
| Docs | 86400s (24h) | Check OpenAPI spec, llms.txt, examples |

### Scoring Weights
| Metric | Weight |
|--------|--------|
| Accuracy | 35% |
| Uptime | 20% |
| Freshness | 15% |
| Latency | 15% |
| Schema stability | 5% |
| Documentation | 5% |
| Trust signals | 5% |

### Pricing Tiers
| Tier | /now | /score | Price |
|------|------|--------|-------|
| Free | 10/day | 5/day | $0 |
| Founding (first 50) | 5,000/day | 2,500/day | $9/mo lifetime |
| Pro | 10,000/day | 5,000/day | $29/mo |
| Enterprise | 100,000/day | 50,000/day | $99/mo |
| x402 pay-per-request | Unlimited | Unlimited | $0.001-0.005/call |

---

## File Map

### Source Code (`src/`)
| File | Purpose |
|------|---------|
| `src/__init__.py` | Package init |
| `src/main.py` | FastAPI app, all routes, lifespan, webhook verification |
| `src/aggregator.py` | Builds `/now` response from sub-modules |
| `src/config.py` | NOW_REFRESH_SECONDS, base config |
| `src/exchange_status.py` | 7 exchange open/close using exchange_calendars |
| `src/volatility.py` | VIX, VVIX, VIX9D, VIX3M, SKEW, term structure |
| `src/events.py` | Economic calendar, FOMC/CPI countdowns |
| `src/billing.py` | Stripe billing, API key gen/register/validate, checkout |
| `src/rate_limit.py` | Tiered rate limiting (free/founding/pro/enterprise) |
| `src/x402.py` | x402 micropayment verify/settle, payment-required header |
| `src/mcp_server.py` | MCP server with 8 tools |

### Monitor (`src/monitor/`)
| File | Purpose |
|------|---------|
| `src/monitor/__init__.py` | Package init |
| `src/monitor/config.py` | MONITORED_APIS dict (7 APIs with endpoints, keys) |
| `src/monitor/scheduler.py` | APScheduler-based probe scheduling |
| `src/monitor/ping_probe.py` | Uptime + latency probe (every 60s) |
| `src/monitor/freshness_probe.py` | Data freshness check (every 5m) |
| `src/monitor/schema_probe.py` | Schema stability detection (every 1h) |
| `src/monitor/accuracy_probe.py` | Forecast snapshot + verification (every 1h) |
| `src/monitor/docs_probe.py` | Documentation quality check (every 24h) |
| `src/monitor/scoring.py` | Composite score computation (weighted) |
| `src/monitor/alerts.py` | Degradation alert detection + check_and_alert() |
| `src/monitor/alert_sender.py` | Telegram notifications with dedup, quiet hours, daily digest |
| `src/monitor/incident_tracker.py` | Incident lifecycle (OPEN->RESOLVED), JSONL history, auto-resolve |
| `src/monitor/store.py` | Dual-write storage (local JSON + Supabase) |
| `src/monitor/supabase_store.py` | Supabase REST client |

### Public Files (`public/`)
| File | Purpose |
|------|---------|
| `public/llms.txt` | Short agent-readable description |
| `public/llms-full.txt` | Complete endpoint docs for agents |
| `public/robots.txt` | Agent-aware robots.txt |
| `public/ai.txt` | AI discovery pointer |
| `public/.well-known/ai-plugin.json` | ChatGPT plugin manifest |
| `public/.well-known/security.txt` | Security contact (RFC 9116) |
| `public/.well-known/tdmrep.json` | W3C TDMRep -- EU AI Act TDM reservation |

### Examples (`examples/`)
| File | Purpose |
|------|---------|
| `examples/trading_agent.py` | AI trading agent using /now + /score |
| `examples/market_monitor.py` | Continuous polling with change alerts |
| `examples/crewai_agent.py` | CrewAI integration demo |
| `examples/langchain_agent.py` | LangChain integration demo |

### Docs (`docs/`)
| File | Purpose |
|------|---------|
| `docs/BUSINESS_CONCEPT.md` | Full business plan, moat, revenue model |
| `docs/IMPLEMENTATION_PLAN.md` | Phase 0-3 build plan |
| `docs/METHODOLOGY.md` | Scoring methodology details |
| `docs/MCP_REGISTRATION.md` | Directory submission status |
| `docs/sample_audit_report.md` | Template for $299-499 API audits |
| `docs/launch_posts.md` | All launch post content + status |
| `docs/reddit_post.txt` | Ready-to-paste post text (HN, DEV.to, Twitter) |
| `docs/reports/2026-03-state-of-financial-data-apis.md` | Report #1: Agent-readiness audit of 7 APIs |
| `docs/reports/2026-03-devto-article.txt` | DEV.to version of Report #1 (plain text for copy-paste) |
| `docs/HEALTHCHECK_SCHEDULE.md` | All probes, intervals, failure handling, manual checks |
| `docs/ISSUE_ESCALATION_PLAYBOOK.md` | Severity levels, known failure scenarios, predetermined fixes |
| `docs/ALERT_REGISTRY.md` | Master inventory of all 9 alert types, channels, dedup rules |
| `docs/START_HERE.md` | Quick reference card for crashed/new sessions (20 lines) |

### MCP Package (`oathscore_mcp/`)
| File | Purpose |
|------|---------|
| `oathscore_mcp/__init__.py` | Package init |
| `oathscore_mcp/__main__.py` | Entry point for `python -m oathscore_mcp` |

### Tests (`tests/`)
| File | Purpose |
|------|---------|
| `tests/test_api.py` | 17 integration tests (all passing as of launch) |

### Infrastructure
| File | Purpose |
|------|---------|
| `Dockerfile` | Python 3.12-slim, uvicorn |
| `Procfile` | Railway process command |
| `requirements.txt` | 7 dependencies (fastapi, uvicorn, httpx, exchange_calendars, pandas, apscheduler, mcp) |
| `pyproject.toml` | Package metadata + pip installable |
| `.gitignore` | Standard Python gitignore |
| `migrations/001_initial.sql` | Supabase schema (6 tables + RLS) |
| `README.md` | GitHub README with examples, pricing, star CTA |
| `.github/workflows/health-check.yml` | GitHub Actions health check |

### Skills (`.claude/skills/`)
| File | Purpose |
|------|---------|
| `.claude/skills/oathscore-session/skill.md` | Session startup/shutdown skill (`/oathscore-session`) |
| `.claude/skills/oathscore-guardian/skill.md` | Zero-trust session guardian (`/oathscore-guardian`) — comprehensive startup, audit, sync, save |
| `.claude/skills/oathscore-audit/skill.md` | Deep forensic audit (`/oathscore-audit`) — full codebase sweep |

### Tracking (`tracking/`)
| File | Purpose |
|------|---------|
| `tracking/OATHSCORE_SESSION.md` | Session state (cumulative, single source of truth) |
| `tracking/PROJECT_TRACKER.md` | Master task list (6 initiatives, priority queue, status counts) |
| `tracking/OWNER_NOTES.md` | Owner<->Claude notification system, GitHub issue sync, free-form notes |

---

## Key Constants & Configuration

### src/config.py
- `BASE_URL` = env `OATHSCORE_BASE_URL` or `https://api.oathscore.dev`
- `CURISTAT_API_URL` = env `CURISTAT_API_URL` or `https://curistat-api-production.up.railway.app`
- `NOW_REFRESH_SECONDS` = 60
- `VIX_PERCENTILE_LOOKBACK_DAYS` = 252
- `EXCHANGES` dict: CME (CME calendar), NYSE, NASDAQ, LSE, EUREX (XETR calendar), TSE (JPX calendar), HKEX
- `VOLATILITY_SYMBOLS`: vix=^VIX, vix9d=^VIX9D, vix3m=^VIX3M, vvix=^VVIX, skew=^SKEW

### src/rate_limit.py
- `TIER_LIMITS` = {"free": (10, 5), "founding": (5000, 2500), "pro": (10000, 5000), "enterprise": (100000, 50000)}
- Tuple = (now_daily_limit, score_daily_limit)
- In-memory tracking by API key (paid) or IP (free), 86400s window

### src/billing.py
- API key format: `os_` + 24 hex bytes (e.g., `os_a1b2c3...`)
- Keys hashed with SHA-256 for storage
- In-memory key store: `_keys[hash] -> {tier, stripe_customer_id, stripe_subscription_id, created_at}`
- Founding slots tracked: `max(0, 50 - _count_tier("founding"))`

### src/x402.py
- `PRICES` = {"now": "0.001", "score": "0.002", "compare": "0.005"} (USDC per call)
- Default network: `base-sepolia` (testnet), production: `base`
- Facilitator URL: `https://x402.org/facilitator`
- NOT YET ACTIVATED (needs X402_ENABLED=true + X402_WALLET_ADDRESS set)

### src/volatility.py
- Yahoo Finance URL: `https://query1.finance.yahoo.com/v8/finance/chart/{symbol}`
- User-Agent: `OathScore/1.0`
- Timeout: 10.0s
- Term structure: contango (vix < vix3m), backwardation (vix > vix3m), flat (equal)

### src/events.py
- `FIXED_EVENTS` (renamed from FIXED_EVENTS_2026): FOMC + CPI dates for 2026 AND 2027
- FOMC 2026: 01-28, 03-18, 05-06, 06-17, 07-29, 09-16, 11-04, 12-16
- FOMC 2027: 01-27, 03-17, 05-05, 06-16, 07-28, 09-22, 11-03, 12-15
- CPI through 2027-12-10
- 20 hardcoded SCHEDULED_EVENTS for 2026-03-04 to 2026-03-28
- Live calendar fallback from Curistat API: `{CURISTAT_API_URL}/api/v1/calendar/week`

### src/monitor/config.py
- ENV VAR NAMES match Railway: `ALPHAVANTAGE_KEY`, `POLYGON_KEY`, `FINNHUB_KEY`, `TWELVEDATA_KEY`, `EODHD_KEY`, `FMP_KEY` (fixed 2026-03-04).
- API base URLs: alphavantage=alphavantage.co, polygon=api.polygon.io, finnhub=finnhub.io/api/v1, twelvedata=api.twelvedata.com, eodhd=eodhd.com/api, fmp=financialmodelingprep.com/api/v3
- Curistat: curistat-api-production.up.railway.app (has_forecasts=True, only one with accuracy tracking)

### src/monitor/scoring.py
- `WEIGHTS` = {accuracy: 0.35, uptime: 0.20, freshness: 0.15, latency: 0.15, schema: 0.05, docs: 0.05, trust: 0.05}
- Minimum 10 pings required before scoring
- Uses last 500 pings for uptime/latency
- Latency brackets: <200ms=100, <500=80, <1000=60, <2000=40, <5000=20, >5000=0
- Freshness brackets: <60s=100, <300s=90, <900s=75, <3600s=50, <86400s=25, >86400s=0 (avg of last 10 checks)
- Trust scoring: base 30 + docs quality 25 + publishes forecasts 25 + uptime >=99% 20
- Letter grades: A+ >=97, A >=93, A- >=90, B+ >=87, B >=83, B- >=80, C+ >=77, C >=73, C- >=70, D >=60, F <60
- Reweights available components (missing components excluded, remaining weights normalized)
- `persist_daily_scores()` writes composite scores to Supabase daily_scores table (runs daily via scheduler)

### src/monitor/alerts.py
- Uptime: <90% WARNING, <50% URGENT, <30% CRITICAL
- Latency: avg >3000ms WARNING
- Consecutive failures: 3+ pings URGENT
- Freshness: >2h WARNING, >6h URGENT, >24h CRITICAL
- Schema changes: WARNING
- `check_and_alert()` runs every 5 min via scheduler — opens incidents, sends Telegram, auto-resolves on recovery

### src/monitor/alert_sender.py
- Telegram only (no email). Uses TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID env vars.
- 4 levels: INFO (daily digest), WARNING (4h cooldown), URGENT (1h cooldown), CRITICAL (no cooldown)
- Quiet hours: 12-6AM ET for WARNING only. URGENT/CRITICAL always send.
- Higher severity overrides cooldown. Dedup state in `data/alert_dedup_state.json`.

### src/monitor/incident_tracker.py
- Lifecycle: OPEN -> RESOLVED (auto-resolve when API recovers)
- History: `data/incident_history.jsonl` (append-only JSONL)
- Active: `data/active_incidents.json`
- `get_patterns(30)` returns APIs with 3+ incidents in 30 days
- `get_source_health(api)` returns uptime%, incident count, mean resolution time

### src/monitor/store.py
- Local JSON dir: `oathscore/data/monitor/` (gitignored)
- Files: pings.json, schemas.json, docs_checks.json, freshness.json, forecast_snapshots.json, active_alerts.json
- MAX_ENTRIES = 10000 per file (trims oldest)
- Dual-write: local JSON + Supabase (Supabase failure doesn't block local write)

### src/monitor/supabase_store.py
- Uses synchronous httpx.Client (singleton)
- Queries default: `order=id.desc`, limit=100
- Headers: apikey + Bearer token + Content-Type + Prefer=return=minimal

### Supabase Tables (from 001_initial.sql)
| Table | Key Columns | Indexes |
|-------|------------|---------|
| pings | api_name, endpoint, status_code, latency_ms, ok, error | idx_pings_api_time(api_name, created_at DESC) |
| schema_snapshots | api_name, endpoint, schema_hash, changed, response_schema(JSONB) | idx_schemas_api(api_name, created_at DESC) |
| freshness_checks | api_name, endpoint, data_timestamp, age_seconds | idx_freshness_api(api_name, created_at DESC) |
| docs_checks | api_name, found(TEXT[]), missing(TEXT[]), docs_accessible, score | -- |
| forecast_snapshots | api_name, forecast_date(DATE), forecast_value, actual_value, accuracy_score | -- |
| daily_scores | api_name, score_date, composite/accuracy/uptime/freshness/latency/schema/docs/trust, grade | idx_scores_api_date(api_name, score_date DESC), UNIQUE(api_name, score_date) |

### /now Response Structure
```
{
  timestamp,
  exchanges: {CME: {status, next, minutes_until}, ...},
  volatility: {vix, vix9d, vix3m, vvix, skew, term_structure},
  events: {next, today_remaining, week_high_impact, fomc_days_until, cpi_days_until},
  data_health: {all_fresh, degraded: [{source, reason}]},
  meta: {version: "1.0.0", source: "oathscore.dev", refresh_interval_seconds: 60}
}
```

### Response Headers on /now
- `Cache-Control: public, max-age=30`
- `X-Cache-Age-Seconds: <int>`
- `X-Next-Refresh-Seconds: <int>`
- `X-RateLimit-Remaining: <int>`

### Anti-Training Headers (ALL responses)
- `X-Robots-Tag: noai, noimageai`
- `X-AI-Training: disallow`
- `TDM-Reservation: 1`

### Middleware Stack (execution order, LIFO)
1. Kill switch -- 503 for all routes except /health when active
2. Bot detection -- blocks 46 training crawler UA patterns, allows 7 discovery bots
3. Honeypots -- 4 fake paths (/wp-admin, /.env, /xmlrpc.php, /api/internal/data-export), returns fake JSON, logs hits
4. Anti-training headers -- X-Robots-Tag, X-AI-Training, TDM-Reservation on all responses
5. Request logging -- REQ method path status latency ua ip

### Cloudflare Configuration (api.oathscore.dev)
- AI Labyrinth: ON (serves fake pages to scrapers)
- Bot Fight Mode: ON (challenges suspicious automated traffic)
- Continuous Script Monitoring: ON
- Hotlink Protection: ON
- Managed robots.txt: ON
- Per-crawler controls: 9 allowed (search/discovery), 21 blocked (training)
- Block AI Bots scope: Off (selective per-crawler control instead)

### GitHub Actions (.github/workflows/health-check.yml)
- Cron: every 6 hours (`0 */6 * * *`)
- Tests against: `https://oathscore-production.up.railway.app`
- Checks: /now (200), /health (print), /scores (print), /now schema validation

### Tests (tests/test_api.py)
- 17 tests against live Railway URL
- Tests: root, now, health, scores, score_unknown (404), score_curistat (200), compare, compare_empty (400), alerts, status, llms_txt, llms_full, robots, ai_txt, ai_plugin, openapi, docs

---

## All Environment Variables (Complete Reference)

| Variable | Used In | Railway Name | Default |
|----------|---------|-------------|---------|
| `OATHSCORE_BASE_URL` | config.py, mcp_server.py | -- | https://api.oathscore.dev |
| `CURISTAT_API_URL` | config.py | -- | https://curistat-api-production.up.railway.app |
| `SUPABASE_URL` | supabase_store.py | SUPABASE_URL | None |
| `SUPABASE_ANON_KEY` | supabase_store.py | SUPABASE_ANON_KEY | None |
| `STRIPE_SECRET_KEY` | billing.py | STRIPE_SECRET_KEY | None |
| `STRIPE_PRICE_FOUNDING` | billing.py | STRIPE_PRICE_FOUNDING | None |
| `STRIPE_PRICE_PRO` | billing.py | STRIPE_PRICE_PRO | None |
| `STRIPE_PRICE_ENTERPRISE` | billing.py | STRIPE_PRICE_ENTERPRISE | None |
| `STRIPE_WEBHOOK_SECRET` | main.py | STRIPE_WEBHOOK_SECRET | None |
| `X402_ENABLED` | x402.py | -- (not set) | "false" |
| `X402_WALLET_ADDRESS` | x402.py | -- (not set) | "" |
| `X402_FACILITATOR_URL` | x402.py | -- (not set) | https://x402.org/facilitator |
| `X402_NETWORK` | x402.py | -- (not set) | "base-sepolia" |
| `ALPHAVANTAGE_KEY` | monitor/config.py | ALPHAVANTAGE_KEY | None |
| `POLYGON_KEY` | monitor/config.py | POLYGON_KEY | None |
| `FINNHUB_KEY` | monitor/config.py | FINNHUB_KEY | None |
| `TWELVEDATA_KEY` | monitor/config.py | TWELVEDATA_KEY | None |
| `EODHD_KEY` | monitor/config.py | EODHD_KEY | None |
| `FMP_KEY` | monitor/config.py | FMP_KEY | None |
| `TELEGRAM_BOT_TOKEN` | alert_sender.py | TELEGRAM_BOT_TOKEN | None |
| `TELEGRAM_CHAT_ID` | alert_sender.py | TELEGRAM_CHAT_ID | None |
| `PORT` | Procfile | PORT (Railway auto) | 8000 |

---

## Known Bugs & Gaps

### FIXED (2026-03-04)
1. ~~ENV VAR NAME MISMATCH~~ — Fixed: monitor/config.py now reads `ALPHAVANTAGE_KEY` etc. matching Railway vars.
2. ~~Example agents is_open bug~~ — Fixed: all 4 examples now use `info.get("status") == "open"`.
3. ~~llms.txt stale~~ — Fixed: 8 tools, correct pricing, founding tier added.
4. ~~llms-full.txt stale~~ — Fixed: free tier shows 10/day, base URL updated.
9. ~~MCP server BASE_URL~~ — Fixed: defaults to `https://api.oathscore.dev`.
- Also fixed: tests/test_api.py and .github/workflows/health-check.yml used old Railway URL.

### FIXED (2026-03-04, batch 2)
5. ~~Freshness scoring not implemented~~ — Fixed: scoring.py now reads freshness.json, scores based on avg age (100 for <60s down to 0 for >86400s).
6. ~~Trust score hardcoded~~ — Fixed: now computed from docs quality (25pts), forecast publishing (25pts), uptime >=99% (20pts), base 30pts.
7. ~~daily_scores table unused~~ — Fixed: `persist_daily_scores()` added to scoring.py, wired into scheduler (runs daily).
8. ~~FOMC/CPI dates hardcoded for 2026~~ — Fixed: events.py renamed to `FIXED_EVENTS`, added projected 2027 dates for both.
10. ~~No CLAUDE.md~~ — Fixed: created CLAUDE.md with project overview, architecture, directory map, env vars, rules.

### Remaining (None)
All 10 audit bugs resolved.

---

## External Services & Credentials

### Railway (Hosting)
- **Dashboard**: https://railway.com (login with GitHub)
- **Service**: OathScore API
- **URL**: https://api.oathscore.dev
- **Cost**: ~$5/mo
- **Deploy**: `railway up` from repo root

### Railway Environment Variables (ALL set)
| Variable | Value/Status | Purpose |
|----------|-------------|---------|
| `SUPABASE_URL` | `https://vehjypmvvanxmzfrwpwa.supabase.co` | Supabase project URL |
| `SUPABASE_ANON_KEY` | `sb_publishable_hiJqHwQw1X9pmK9gUztt_g_olwtYgOj` | Supabase public key |
| `ALPHAVANTAGE_KEY` | `5HJHGXZPRSTCOZZ3` | Alpha Vantage API |
| `POLYGON_KEY` | (set, check Railway) | Polygon.io API |
| `FINNHUB_KEY` | `d6jsgkpr01qkvh5r6n1gd6jsgkpr01qkvh5r6n203` | Finnhub API |
| `TWELVEDATA_KEY` | `1f843fd9afa846efbd2bf23e34e53aac` | Twelve Data API |
| `EODHD_KEY` | `69a7c9588da469.11770448` | EODHD API |
| `FMP_KEY` | `RRBV3YYZ0YXUYwDvxAKzjCNkmabMMFSI` | Financial Modeling Prep |
| `STRIPE_SECRET_KEY` | `sk_live_51T7GugE6Mysiw6jD...` (live) | Stripe billing |
| `STRIPE_PRICE_FOUNDING` | `price_1T7I4DE6Mysiw6jDcghnXHYf` | Founding tier price ID |
| `STRIPE_PRICE_PRO` | `price_1T7I3cE6Mysiw6jD3T5SB0O8` | Pro tier price ID |
| `STRIPE_PRICE_ENTERPRISE` | `price_1T7I2jE6Mysiw6jD7oJWTvjr` | Enterprise tier price ID |
| `STRIPE_WEBHOOK_SECRET` | `whsec_tq1zQRXD58AWJD3UnxagXb3nBVY9QDwP` | Webhook signature verification |

### Stripe (Billing)
- **Dashboard**: https://dashboard.stripe.com
- **Account**: OathScore (under Curistat LLC)
- **Mode**: LIVE (real money)
- **Publishable key**: `pk_live_51T7GugE6Mysiw6jDnYQIryuNsfGtYX0An9DGd9amzAaC9uXlcpb6FnxJW8ccfs1sk3Xz3l7CwgV6j3dhKwDLx0ks00vXDaHG4y`
- **Products**: Founding ($9/mo), Pro ($29/mo), Enterprise ($99/mo)
- **Webhook**: 1 destination, 3 events (checkout.session.completed, customer.subscription.deleted, invoice.payment_failed)
- **Webhook URL**: https://api.oathscore.dev/webhooks/stripe

### Supabase (Database)
- **Dashboard**: https://supabase.com/dashboard
- **Project URL**: https://vehjypmvvanxmzfrwpwa.supabase.co
- **Tables**: api_pings, api_freshness, api_schema, api_accuracy, api_docs, api_scores
- **RLS**: Enabled on all tables (anon can SELECT, service_role can INSERT)

### GitHub
- **Repo**: https://github.com/moxiespirit/oathscore
- **Topics**: mcp, trading, finance, api, vix, market-data, ai-agents
- **Actions**: health check workflow (`.github/workflows/health.yml`)

### Domain
- **api.oathscore.dev** — pointed to Railway via CNAME
- **oathscore.dev** — (domain registered, DNS managed wherever you bought it)

---

## Monitored APIs (7)

| API | Category | Key Set | Status |
|-----|----------|---------|--------|
| Alpha Vantage | Equities/macro | Yes | Monitoring |
| Polygon.io | Market data | Yes | Monitoring |
| Finnhub | Multi-asset | Yes | Monitoring |
| Twelve Data | Market data | Yes | Monitoring |
| EODHD | Historical data | Yes | Monitoring |
| Financial Modeling Prep | Fundamentals | Yes | Monitoring |
| Curistat | Futures volatility | No key needed | Monitoring |

Scores publish after 30 days of baseline data collection.

---

## MCP Directory Submissions

| Directory | Method | Status | Link |
|-----------|--------|--------|------|
| Glama.ai | Browser form | **Approved & Listed** | Listed |
| mcp.so | GitHub issue | Submitted, waiting | https://github.com/chatmcp/mcpso/issues/668 |
| punkpeye/awesome-mcp-servers | PR | Submitted, waiting | https://github.com/punkpeye/awesome-mcp-servers/pull/2694 |
| mcpservers.org | Browser form | Submitted, waiting | -- |
| PulseMCP | Deferred | Auto-ingests from official registry | -- |
| Official MCP Registry | Deferred | Needs npm packaging | -- |

---

## Launch / Marketing Status

| Channel | Status | Notes |
|---------|--------|-------|
| Hacker News | **Posted** | Show HN link post to GitHub |
| DEV.to | **Posted** | Full article "Building the Trust Layer for AI Trading Agents" |
| r/algotrading | Blocked | Account needs 50 subreddit karma |
| r/LocalLLaMA | Blocked | Account needs karma |
| r/ClaudeAI | Blocked | Account needs karma |
| Product Hunt | Skipped | Not a fit for this product |
| Twitter/X | Not posted | Draft in docs/reddit_post.txt |

---

## Completed Tasks

| # | Task | Date |
|---|------|------|
| -- | Phase 0: /now endpoint + agent discovery stack | 2026-03-03 |
| -- | Phase 1: Monitoring probes (ping, freshness, schema, accuracy, docs) | 2026-03-03 |
| -- | Phase 2: Scoring engine + /score + /compare + /alerts | 2026-03-03 |
| 6 | Tighten free tier rate limits (10/day now, 5/day score) | 2026-03-04 |
| 7 | Stripe billing + API key system (live mode) | 2026-03-04 |
| 8 | x402 micropayment support | 2026-03-04 |
| 9 | Sample API audit report template | 2026-03-04 |
| 10 | Founding member pricing + signup flow | 2026-03-04 |
| 11 | Launch posts (HN + DEV.to) | 2026-03-04 |
| 12 | DEV.to article published | 2026-03-04 |
| 13 | Show HN submitted | 2026-03-04 |
| 14 | Example agents (4: trading, monitor, crewai, langchain) | 2026-03-04 |
| -- | Supabase integration + migration | 2026-03-04 |
| -- | All 6 API keys registered in Railway | 2026-03-04 |
| -- | MCP directory submissions (4 directories) | 2026-03-04 |
| -- | Stripe webhook with signature verification | 2026-03-04 |
| -- | GitHub topics added | 2026-03-04 |
| -- | README star CTA | 2026-03-04 |

## Pending Tasks

**Full task list: `tracking/PROJECT_TRACKER.md`** (single source of truth for all tasks)

**Next up (from Priority Queue):**
1. ~~5.4-5.5 — Bot detection + webhook rate limiting~~ — DONE (2026-03-13)
2. First traffic analysis report — after 2026-03-20 (need 1+ week log data)
3. 3.9 — Sponsored comparisons — MONTH 1
4. 3.10 — Monthly report — MONTH 1
5. 5.6-5.9 — Agent reputation + enforcement — WHEN PAYING CUSTOMERS

**Cannot do now (tracked as GitHub issues):**
- TLS fingerprinting (JA3/JA4): Requires Cloudflare Business plan ($200+/mo). Free tier does not expose JA3/JA4 headers.
- Reverse DNS verification: Adds 50-200ms latency. Cloudflare per-crawler controls already verify bot identity at edge. Redundant at current scale.
- Traffic analysis report: Needs 1+ week of accumulated log data. Earliest: 2026-03-20.

---

## Decisions Made

1. **Free tier tightened** — 10/day /now, 5/day /score (was unlimited). Drives upgrades.
2. **Founding tier** — $9/mo lifetime for first 50 subscribers. Creates urgency.
3. **x402 over traditional billing for agents** — agents can pay per request without signup.
4. **No npm packaging yet** — deferred official MCP registry submission.
5. **Skip Product Hunt** — not a fit for B2D/agent tooling.
6. **Skip Reddit** — no karma, focus on HN + DEV.to + directories.
7. **Stripe under Curistat LLC** — single legal entity for both products.
8. **Supabase free tier** — sufficient for monitoring data storage.
9. **Railway $5/mo** — cheapest viable hosting with custom domains.
10. **Dual-write storage** — local JSON (fast) + Supabase (persistent). Resilient.

---

## Owner Instructions

### Active Rules
1. Revenue is priority — "no revenue won't work. the goal is to produce income asap"
2. Keep it simple — "besides stripe what else is needed for us to just be live. a lot of this is extra"
3. Don't approach companies for audits yet — need to write up an actual audit report first (done: sample_audit_report.md)
4. Sponsored comparisons + monthly report = Month 1, not launch
5. No Twitter account for now

### Historical Context
- Owner created Stripe account under "Founding Member" name initially, renamed to OathScore
- Reddit account (laguia5) has zero karma — all subreddits auto-remove posts
- Owner prefers step-by-step guidance for external platform navigation (Stripe, Reddit, etc.)
- When providing copy-paste text, write to a .txt file — markdown renders in Claude's output

---

## Build Timeline

| Date | Milestone |
|------|-----------|
| 2026-03-03 | Phase 0: /now endpoint, agent discovery, Docker, Railway deploy |
| 2026-03-03 | Phase 1: 5 monitoring probes, /scores endpoint |
| 2026-03-03 | Phase 2: Scoring engine, /compare, /alerts, MCP 8 tools |
| 2026-03-03 | Custom domain api.oathscore.dev live |
| 2026-03-03 | 17/17 integration tests passing |
| 2026-03-04 | Supabase persistent storage connected |
| 2026-03-04 | All 6 API provider keys registered |
| 2026-03-04 | MCP directories submitted (Glama approved) |
| 2026-03-04 | Stripe billing live (real money) |
| 2026-03-04 | x402 micropayment code deployed |
| 2026-03-04 | Launch posts: HN + DEV.to |
| 2026-03-04 | Stripe webhook with signature verification |
| 2026-03-04 | 4 example agents published |

---

## Session Log

| Date | Session | Key Actions |
|------|---------|-------------|
| 2026-03-03 | S1 | Built entire product from scratch: Phase 0 (API), Phase 1 (monitoring), Phase 2 (scoring). Deployed to Railway. Custom domain. 17 tests passing. |
| 2026-03-04 | S2 | Supabase integration. API keys for all 6 providers. MCP directory submissions (4). Stripe billing (live). x402 micropayments. Launch posts (HN + DEV.to). Example agents (4). Webhook security. GitHub topics. |
| 2026-03-13 | S4 | AI bot defense hardening: robots.txt 22->55 blocked crawlers, main.py 21->46 UA patterns, honeypot middleware (4 paths), TDM-Reservation header, tdmrep.json route, Cloudflare config (AI Labyrinth, Bot Fight Mode, per-crawler controls). Deployed via `railway up`. |
| 2026-03-05 | S3 | Alert system (alert_sender.py, incident_tracker.py). Expanded alerts.py thresholds. Wired into scheduler. Operational docs (HEALTHCHECK_SCHEDULE, ISSUE_ESCALATION_PLAYBOOK, ALERT_REGISTRY, OWNER_NOTES). Telegram-only (no SendGrid). |

---

## Next Session Startup

Run `/oathscore-guardian`. It automates all of this:

1. Live date check + re-read CLAUDE.md
2. Load session state, tracker, owner notes, operational docs
3. Zero-trust verification (env vars, URLs, scheduler, alerts, scoring, calendar, live API)
4. Sync GitHub issues + MCP directory status
5. Present briefing + wait for owner direction

Fallback (if skill unavailable): read `docs/START_HERE.md` for manual steps.
