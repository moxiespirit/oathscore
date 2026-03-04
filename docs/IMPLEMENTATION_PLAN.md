# OathScore — Implementation Plan

**Created**: 2026-03-03
**Status**: Planning

---

## Phase 0: Foundation (Weekend Project)

**Goal**: `/now` endpoint live and returning real data.

### Owner Tasks

| # | Task | Time | Cost | Notes |
|---|------|------|------|-------|
| O-0.1 | Register oathscore.dev domain | 15 min | $12/year | Or .io if .ai unavailable at good price |
| O-0.2 | Create Cloudflare account (or add domain to existing) | 10 min | $0 | Free plan sufficient |
| O-0.3 | Create GitHub repo (public) | 5 min | $0 | Public repo IS the marketing |
| O-0.4 | Point domain DNS to Cloudflare | 10 min | $0 | Nameservers swap |
| O-0.5 | Test `/now` endpoint after deployment | 10 min | $0 | curl + verify response |

**Owner total: ~50 min, $12**

### Claude Tasks

| # | Task | Time | Token Cost | Dependencies |
|---|------|------|-----------|-------------|
| C-0.1 | Build `/now` data aggregator (Python) | 2h | ~$2-3 | None |
| C-0.2 | Build Cloudflare Worker to serve `/now` | 1h | ~$1-2 | C-0.1 |
| C-0.3 | Write `llms.txt` and `llms-full.txt` | 30 min | ~$0.50 | C-0.1 |
| C-0.4 | Write `.well-known/ai-plugin.json` | 15 min | ~$0.25 | C-0.1 |
| C-0.5 | Write OpenAPI spec for `/now` | 30 min | ~$0.50 | C-0.1 |
| C-0.6 | Create `robots.txt` (agent-aware) | 15 min | ~$0.25 | None |
| C-0.7 | Deploy to Cloudflare Workers | 30 min | ~$0.50 | O-0.2, C-0.2 |
| C-0.8 | End-to-end test | 30 min | ~$0.50 | C-0.7 |

**Claude total: ~5.5h, ~$5-7**

### `/now` Data Sources (All Free)

| Data Field | Source | Method | Refresh |
|-----------|--------|--------|---------|
| Exchange status (CME, NYSE, NASDAQ) | `exchange_calendars` Python lib | Schedule-derived | Static (check holidays daily) |
| Exchange status (LSE, EUREX, TSE, HKEX) | `exchange_calendars` Python lib | Schedule-derived | Static |
| VIX, VIX9D, VIX3M, VVIX | Yahoo Finance (yfinance) | HTTP fetch | Every 60s during market hours |
| SKEW | Yahoo Finance | HTTP fetch | Every 60s |
| Term structure (contango/backwardation) | Computed from VIX vs VIX3M | Local calc | Every 60s |
| VIX 1Y percentile | Computed from historical VIX CSV | Local calc | Daily |
| CRC regime | Curistat API (free /health or internal) | HTTP fetch | Every 5 min |
| Economic events | Curistat calendar or FRED | HTTP fetch | Every 15 min |
| Event countdown | Computed from calendar + current time | Local calc | Every 60s |
| FOMC/CPI countdown | Computed from known schedule | Local calc | Daily |
| Data health | Self-monitoring of all above sources | Internal | Every 60s |

### Deliverables

- [ ] `/now` endpoint returning full JSON schema
- [ ] `llms.txt` at domain root
- [ ] `llms-full.txt` at domain root
- [ ] `.well-known/ai-plugin.json`
- [ ] OpenAPI 3.0.3 spec at `/api/discover`
- [ ] `robots.txt` with agent-aware rules
- [ ] README.md on GitHub repo

---

## Phase 1: Monitoring Infrastructure (Week 1)

**Goal**: OathScore collecting baseline data on 7 financial APIs.

### Owner Tasks

| # | Task | Time | Cost | Notes |
|---|------|------|------|-------|
| O-1.1 | Register free tier accounts at Alpha Vantage, Polygon, Finnhub, Twelve Data, EODHD, FMP | 1h | $0 | Need API keys for each |
| O-1.2 | Store API keys in Railway env vars | 15 min | $0 | Never in code |
| O-1.3 | Review monitoring dashboard after 24h | 15 min | $0 | Sanity check |

**Owner total: ~1.5h, $5/mo (Railway)**

### Claude Tasks

| # | Task | Time | Token Cost | Dependencies |
|---|------|------|-----------|-------------|
| C-1.1 | Build uptime/latency monitor (pings every 60s) | 2h | ~$2-3 | O-1.1 |
| C-1.2 | Build freshness checker (data age tracking) | 1.5h | ~$1.50-2 | O-1.1 |
| C-1.3 | Build accuracy recorder (snapshot forecasts for later comparison) | 2h | ~$2-3 | O-1.1 |
| C-1.4 | Build accuracy verifier (compare yesterday's forecast to actual) | 1.5h | ~$1.50-2 | C-1.3 |
| C-1.5 | Build schema change detector | 1h | ~$1-1.50 | O-1.1 |
| C-1.6 | Build documentation checker (OpenAPI, llms.txt existence) | 30 min | ~$0.50 | None |
| C-1.7 | Set up Supabase tables for all metrics | 1h | ~$1-1.50 | None |
| C-1.8 | Deploy monitoring service to Railway | 1h | ~$1-1.50 | C-1.1 through C-1.7 |
| C-1.9 | Build simple status page (JSON endpoint showing all monitors) | 30 min | ~$0.50 | C-1.8 |

**Claude total: ~11h, ~$10-14**

### Supabase Schema (Draft)

```sql
-- Raw ping results
CREATE TABLE pings (
  id BIGSERIAL PRIMARY KEY,
  api_name TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  status_code INT,
  latency_ms INT,
  timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Daily accuracy snapshots
CREATE TABLE forecast_snapshots (
  id BIGSERIAL PRIMARY KEY,
  api_name TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  forecast_date DATE NOT NULL,
  forecast_value JSONB NOT NULL,
  actual_value JSONB,  -- filled in next day
  accuracy_score FLOAT,  -- computed after actual available
  snapshot_time TIMESTAMPTZ DEFAULT NOW()
);

-- Data freshness checks
CREATE TABLE freshness_checks (
  id BIGSERIAL PRIMARY KEY,
  api_name TEXT NOT NULL,
  claimed_freshness TEXT,  -- what the API says
  actual_age_seconds INT,  -- what we measured
  timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Schema snapshots (detect breaking changes)
CREATE TABLE schema_snapshots (
  id BIGSERIAL PRIMARY KEY,
  api_name TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  response_schema_hash TEXT NOT NULL,
  response_schema JSONB NOT NULL,
  changed_from_previous BOOLEAN DEFAULT FALSE,
  timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Computed daily scores
CREATE TABLE daily_scores (
  id BIGSERIAL PRIMARY KEY,
  api_name TEXT NOT NULL,
  score_date DATE NOT NULL,
  accuracy_score FLOAT,
  uptime_score FLOAT,
  freshness_score FLOAT,
  latency_score FLOAT,
  schema_score FLOAT,
  docs_score FLOAT,
  trust_signals_score FLOAT,
  composite_score FLOAT,
  UNIQUE(api_name, score_date)
);
```

### What Gets Monitored Per API

| API | Endpoints to Monitor | Has Forecasts? | Accuracy Method |
|-----|---------------------|----------------|-----------------|
| Curistat | /forecast/today, /regime, /signals | YES | Compare CVN rating + range to actual |
| Alpha Vantage | /query?function=GLOBAL_QUOTE, TIME_SERIES_DAILY | NO (data only) | Freshness + completeness only |
| Polygon | /v1/marketstatus/now, /v2/aggs | NO (data only) | Freshness + completeness + compare to reference |
| Finnhub | /api/v1/quote, /api/v1/calendar/economic | Partial (calendar) | Event accuracy (did it happen when claimed?) |
| Twelve Data | /time_series, /quote | NO (data only) | Freshness + completeness |
| EODHD | /api/real-time, /api/eod | NO (data only) | Freshness + completeness |
| FMP | /api/v3/quote, /api/v3/income-statement | NO (data only) | Freshness + completeness |

---

## Phase 2: Scoring Engine (Week 2)

**Goal**: OathScore computing and serving composite scores.

### Owner Tasks

| # | Task | Time | Cost | Notes |
|---|------|------|------|-------|
| O-2.1 | Review composite scores — do they match your intuition? | 1h | $0 | Gut check: is Alpha Vantage really a 71? |

**Owner total: ~1h, $0**

### Claude Tasks

| # | Task | Time | Token Cost | Dependencies |
|---|------|------|-----------|-------------|
| C-2.1 | Build scoring algorithm (weighted composite) | 2h | ~$2-3 | Phase 1 data |
| C-2.2 | Build `/api/score/{api_name}` endpoint | 1.5h | ~$1.50-2 | C-2.1 |
| C-2.3 | Build `/api/compare?apis=a,b` endpoint | 1.5h | ~$1.50-2 | C-2.1 |
| C-2.4 | Build `/api/alerts` endpoint (active degradations) | 1h | ~$1-1.50 | C-2.1 |
| C-2.5 | Integrate `trust_scores` into `/now` response | 1h | ~$1-1.50 | C-2.2 |
| C-2.6 | Generate OpenAPI spec for all scoring endpoints | 1h | ~$1-1.50 | C-2.2, C-2.3, C-2.4 |
| C-2.7 | Deploy scoring engine to Cloudflare Workers | 30 min | ~$0.50 | All above |
| C-2.8 | Write scoring methodology doc (public — transparency is the product) | 1h | ~$1-1.50 | C-2.1 |

**Claude total: ~9.5h, ~$9-12**

### Score Calculation Detail

```python
def compute_composite_score(api_name: str, window_days: int = 30) -> float:
    """
    Composite OathScore (0-100).

    Components:
    - Accuracy (35%):  For forecast APIs: MAE, directional accuracy, calibration
                       For data APIs: completeness, correctness vs reference
    - Uptime (20%):    % of pings returning 2xx in window
    - Freshness (15%): % of checks where data age < claimed freshness
    - Latency (15%):   Normalized P50 latency (lower = better)
    - Schema (5%):     0 breaking changes = 100, each change = -20
    - Docs (5%):       Has OpenAPI + llms.txt + examples = 100
    - Trust (5%):      Publishes accuracy data + signs responses + ETag support
    """
    weights = {
        'accuracy': 0.35,
        'uptime': 0.20,
        'freshness': 0.15,
        'latency': 0.15,
        'schema': 0.05,
        'docs': 0.05,
        'trust_signals': 0.05,
    }

    scores = {
        'accuracy': compute_accuracy_score(api_name, window_days),
        'uptime': compute_uptime_score(api_name, window_days),
        'freshness': compute_freshness_score(api_name, window_days),
        'latency': compute_latency_score(api_name, window_days),
        'schema': compute_schema_score(api_name, window_days),
        'docs': compute_docs_score(api_name),
        'trust_signals': compute_trust_score(api_name),
    }

    composite = sum(scores[k] * weights[k] for k in weights)
    return round(composite, 1)
```

### Score Response Schema

```json
{
  "api": "curistat",
  "score": 94,
  "grade": "A",
  "components": {
    "accuracy": {"score": 97, "weight": "35%", "detail": "30d MAE: 0.8, direction: 82%, r: 0.78"},
    "uptime": {"score": 99, "weight": "20%", "detail": "99.2% uptime (30d)"},
    "freshness": {"score": 95, "weight": "15%", "detail": "avg data age: 45s, claimed: 60s"},
    "latency": {"score": 88, "weight": "15%", "detail": "P50: 120ms, P95: 340ms, P99: 890ms"},
    "schema": {"score": 100, "weight": "5%", "detail": "0 breaking changes (30d)"},
    "docs": {"score": 90, "weight": "5%", "detail": "OpenAPI: yes, llms.txt: yes, examples: partial"},
    "trust_signals": {"score": 85, "weight": "5%", "detail": "accuracy endpoint: yes, signing: yes, ETag: no"}
  },
  "history": {
    "30d_avg": 93,
    "90d_avg": null,
    "trend": "stable"
  },
  "monitored_since": "2026-03-10",
  "last_updated": "2026-03-03T20:30:00Z",
  "methodology": "https://oathscore.dev/docs/methodology"
}
```

---

## Phase 3: Distribution (Week 2-3)

**Goal**: Agents can discover OathScore.

### Owner Tasks

| # | Task | Time | Cost | Notes |
|---|------|------|------|-------|
| O-3.1 | Review all submission descriptions before they go out | 30 min | $0 | Final approval |

**Owner total: ~30 min, $0**

### Claude Tasks

| # | Task | Time | Token Cost | Dependencies |
|---|------|------|-----------|-------------|
| C-3.1 | Build OathScore MCP server (FastMCP, 5 tools) | 2h | ~$2-3 | Phase 2 |
| C-3.2 | Submit to Glama | 15 min | $0 | C-3.1 |
| C-3.3 | Submit to Smithery | 15 min | $0 | C-3.1 |
| C-3.4 | Submit to mcpservers.org | 15 min | $0 | C-3.1 |
| C-3.5 | Submit PRs to awesome-mcp-servers (wong2 + punkpeye) | 30 min | $0 | C-3.1 |
| C-3.6 | Submit to Fluora/MonetizedMCP | 15 min | $0 | C-3.1 |
| C-3.7 | Submit PRs to awesome-fintech-api, awesome-quant | 30 min | $0 | Phase 2 |
| C-3.8 | Submit to PulseMCP + MCP Server Finder | 15 min | $0 | C-3.1 |
| C-3.9 | Update llms.txt and llms-full.txt with scoring endpoints | 15 min | ~$0.25 | Phase 2 |
| C-3.10 | Create integration examples (CrewAI, LangChain) in README | 30 min | ~$0.50 | C-3.1 |

**Claude total: ~5h, ~$5-7**

### Submission Descriptions (Ready to Use)

**For MCP directories:**
```
oathscore — The trust layer for AI agents. Two products: (1) /now endpoint
returning real-time world state (exchange status, volatility, events, regime)
in one call. (2) Independent quality ratings for financial data APIs — accuracy,
uptime, freshness, latency, scored 0-100. Agents check OathScore before
committing to any data source. 5 MCP tools. Free tier available.
```

**For fintech/trading lists:**
```
OathScore — Independent quality ratings for financial data APIs. Continuously
monitors accuracy, uptime, freshness, and latency of APIs like Alpha Vantage,
Polygon, Finnhub, Curistat, and more. Composite score 0-100. Plus a /now
endpoint providing unified market context (exchange status, VIX, events,
regime) in a single call. Built for AI trading agents. Free tier: 100
calls/day. MCP server available.
```

---

## Phase 4: Monetization (Month 2+)

**Goal**: Revenue from both products.

### Owner Tasks

| # | Task | Time | Cost | Notes |
|---|------|------|------|-------|
| O-4.1 | Create Stripe account for OathScore (SEPARATE from Curistat) | 30 min | $0 | Transaction fees only |
| O-4.2 | Contact Alpha Vantage, Polygon, Finnhub about Verified badges | 2h | $0 | Email outreach |
| O-4.3 | Set pricing for badges ($49/$99/$199 tiers) | 30 min | $0 | Review Claude's recommendation |

**Owner total: ~3h, Stripe transaction fees**

### Claude Tasks

| # | Task | Time | Token Cost | Dependencies |
|---|------|------|-----------|-------------|
| C-4.1 | Add Stripe usage-based billing for /now and score queries | 3h | ~$3-5 | O-4.1 |
| C-4.2 | Build API key system (free + paid tiers) | 2h | ~$2-3 | C-4.1 |
| C-4.3 | Build "OathScore Verified" badge system | 2h | ~$2-3 | C-4.1 |
| C-4.4 | Build webhook alert product (score change notifications) | 2h | ~$2-3 | Phase 2 |
| C-4.5 | Add rate limiting per tier | 1h | ~$1-1.50 | C-4.2 |
| C-4.6 | Build API provider self-service (claim your API, add context) | 2h | ~$2-3 | C-4.3 |

**Claude total: ~12h, ~$12-18**

### Pricing Tiers

**For Agents (consumers of scores):**

| Tier | /now Calls | Score Queries | Compare | Webhooks | Price |
|------|-----------|---------------|---------|----------|-------|
| Free | 100/day | 50/day | 5/day | 0 | $0 |
| Pro | 10,000/day | 5,000/day | 500/day | 10 | $29/mo |
| Enterprise | 100,000/day | 50,000/day | 5,000/day | 100 | $99/mo |

**For API Providers (verified badges):**

| Tier | Features | Price |
|------|----------|-------|
| Basic | OathScore Verified badge, public score page | $49/mo |
| Pro | Badge + detailed analytics on how agents perceive your API | $99/mo |
| Enterprise | Badge + analytics + custom benchmarks + priority re-scoring | $199/mo |

---

## Phase 5: Scale & Moat (Month 3-6)

**Goal**: 30+ APIs rated, deep historical data, become the default trust layer.

### Owner Tasks

| # | Task | Time | Cost | Notes |
|---|------|------|------|-------|
| O-5.1 | Review monthly "State of Financial Data APIs" report | 30 min/mo | $0 | Claude drafts, Owner approves |
| O-5.2 | Outreach to API providers for badge sales | 1h/mo | $0 | Warm emails to rated APIs |

**Owner total: ~1.5h/month, $0**

### Claude Tasks

| # | Task | Time | Token Cost | Dependencies |
|---|------|------|-----------|-------------|
| C-5.1 | Add Tier 2 APIs (FRED, Treasury, BLS — 10 sources) | 4h | ~$4-6 | Phase 1 infrastructure |
| C-5.2 | Add Tier 3 APIs (news, alternative data — 10 sources) | 4h | ~$4-6 | Phase 1 infrastructure |
| C-5.3 | Add global exchanges to /now (TSE, HKEX, LSE, EUREX, ASX) | 2h | ~$2-3 | Phase 0 |
| C-5.4 | Build public dashboard (optional, human-readable scores) | 6h | ~$6-9 | Phase 2 |
| C-5.5 | Add news sentiment to /now v2 (if demand) | 4h | ~$4-6 | TBD |
| C-5.6 | Publish monthly "State of Financial Data APIs" report | 2h/mo | ~$2-3/mo | Phase 2 data |
| C-5.7 | Add x402 payment support (when market ready) | 3h | ~$3-5 | Owner decision |

**Claude total: ~25h + 2h/month, ~$25-38 + $2-3/month**

---

## Cumulative Investment

### To MVP (Phase 0-3): 3 weeks

| | Owner Time | Owner Cost | Claude Time | Claude Tokens |
|---|-----------|-----------|-------------|---------------|
| Phase 0 | 50 min | $12 | 5.5h | ~$5-7 |
| Phase 1 | 1.5h | $5/mo | 11h | ~$10-14 |
| Phase 2 | 1h | $0 | 9.5h | ~$9-12 |
| Phase 3 | 30 min | $0 | 5h | ~$5-7 |
| **Total** | **~4h** | **$12 + $5/mo** | **~31h** | **~$29-40** |

### To Revenue (Add Phase 4): +2 weeks

| | Owner Time | Owner Cost | Claude Time | Claude Tokens |
|---|-----------|-----------|-------------|---------------|
| Phase 4 | 3h | Stripe fees | 12h | ~$12-18 |
| **Cumulative** | **~7h** | **$12 + $5/mo** | **~43h** | **~$41-58** |

### To Scale (Add Phase 5): +3 months

| | Owner Time | Owner Cost | Claude Time | Claude Tokens |
|---|-----------|-----------|-------------|---------------|
| Phase 5 | 1.5h/mo | $0 | 25h + 2h/mo | ~$25-38 + $2-3/mo |
| **Cumulative** | **~11.5h** | **$12 + $5/mo** | **~68h** | **~$66-96** |

### Monthly Operating Costs

| Item | Cost | Notes |
|------|------|-------|
| Domain (oathscore.dev) | ~$1/mo | $12/year |
| Cloudflare Workers | $0-5/mo | Free under 100K req/day |
| Railway (monitoring) | $5/mo | Cron + monitoring service |
| Supabase | $0/mo | Free tier (500MB) |
| Free tier API keys | $0/mo | All monitoring on free tiers |
| **Total** | **$6-11/mo** | |

---

## File Structure

```
oathscore/
  README.md                     -- GitHub landing page (IS the marketing)
  docs/
    IMPLEMENTATION_PLAN.md      -- THIS FILE
    METHODOLOGY.md              -- Public scoring methodology (transparency)
    BUSINESS_CONCEPT.md         -- Internal strategy (from brainstorm session)
  src/
    now/
      worker.js                 -- Cloudflare Worker for /now endpoint
      aggregator.py             -- Data gathering cron job
      exchange_status.py        -- Exchange open/close from schedules
      volatility.py             -- VIX/VVIX/term structure fetcher
      events.py                 -- Economic calendar + countdown
    scoring/
      worker.js                 -- Cloudflare Worker for /score endpoints
      composite.py              -- Composite score calculator
      accuracy.py               -- Accuracy verification logic
      freshness.py              -- Data freshness checker
    shared/
      supabase.py               -- Database client
      config.py                 -- API keys, endpoints, constants
  monitoring/
    monitor.py                  -- Main monitoring service (runs on Railway)
    pingers.py                  -- Uptime/latency checks
    schema_checker.py           -- Schema change detection
    docs_checker.py             -- Documentation quality checks
  mcp/
    oathscore_mcp.py            -- FastMCP server (5 tools)
    README.md                   -- MCP integration guide
  public/
    llms.txt                    -- Agent-readable product description
    llms-full.txt               -- Complete endpoint docs
    ai.txt                      -- Discovery pointer
    robots.txt                  -- Agent-aware rules
    .well-known/
      ai-plugin.json            -- ChatGPT plugin manifest
  .github/
    workflows/
      monitor.yml               -- GitHub Actions backup for monitoring (optional)
```

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-03 | Name: OathScore | "Every API makes promises. OathScore checks the receipts." |
| 2026-03-03 | Separate entity from Curistat | Independence IS the product. Agents won't trust ratings from a competitor. |
| 2026-03-03 | Repository-first, no website | Agents discover via MCP registries and llms.txt, not Google. README is the landing page. |
| 2026-03-03 | Cloudflare Workers for serving | $0/month at 100K req/day. Can't beat free. |
| 2026-03-03 | Railway for monitoring | $5/month, already familiar from Curistat. |
| 2026-03-03 | Supabase for storage | Free tier (500MB), already familiar from Curistat. |
| 2026-03-03 | Accuracy weighted 35% | Agents buy data for decisions. Accuracy is the only thing that matters at the end of the day. |
| 2026-03-03 | 30 days before scores populate | Need baseline data. Rushing scores with insufficient data would undermine credibility. |
| 2026-03-03 | x402 deferred | Same as Curistat — Stripe usage-based billing first. Revisit when market ready. |

---

*This plan requires Owner review and approval before implementation begins.*
