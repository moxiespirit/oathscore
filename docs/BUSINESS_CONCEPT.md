# Agent Trust Layer — Business Concept & Implementation Plan

**Status**: DRAFT — Owner Review Required
**Created**: 2026-03-03
**Context**: Brainstorming session identified two complementary products that fill confirmed market gaps. Research validated that neither exists today.

---

## The Concept in One Sentence

**A machine-readable trust layer that tells AI agents what's happening right now and who to believe about it.**

---

## Two Products, One Flywheel

### Product 1: `/now` — "The Agent's Homepage"

A single API endpoint returning the current state of the world for trading agents. Exchange status, volatility readings, economic event countdowns, regime classification, data source health — all in one call.

**Why it wins:** An agent today needs 4-6 API calls (Polygon + Yahoo + Finnhub + calendar + custom logic) to assemble the context it needs before making a decision. `/now` does that assembly once and serves it to thousands of agents. Every agent session starts here.

**The "cat video" economics:** Each call is worth $0.001-0.005. But an agent polling every 60 seconds during a 6.5-hour trading day = 390 calls/day. 1,000 agents = 390,000 calls/day. At $0.003/call = $1,170/day = $35K/month. From a cached JSON blob that costs $0/month to serve on Cloudflare Workers.

### Product 2: OathScore — "The Credit Bureau for Data APIs"

An independent service that continuously monitors, backtests, and scores data APIs that agents rely on. Agents check OathScore before committing to any data source. APIs seek OathScore verification for credibility.

**Why it wins:** Everyone is building "Know Your Agent" (KYA) to verify the buyer. Nobody is building "Know Your API" to verify the seller. Glama scores MCP code quality. RapidAPI has human reviews. Nobody independently verifies whether the data an API returns is actually accurate.

**The moat:** Historical accuracy data accumulates over time. A competitor starting in 2027 has zero history. 12 months of independently verified accuracy logs for 50+ APIs is unreproducible without a time machine.

### The Flywheel

```
Agent discovers /now → uses it daily (habit) → /now includes OathScore scores
→ agent trusts OathScore ratings → picks Curistat for volatility (highest rated)
→ Curistat gains users → other APIs want OathScore verification → more APIs rated
→ more agents trust OathScore → more agents discover /now → repeat
```

Curistat benefits directly: it's the first API rated, it scores well (r=0.7807 is verifiable), and every agent that starts at `/now` sees Curistat recommended for volatility data.

---

## Product 1 Spec: `/now` Endpoint

### Response Schema (v1)

```json
{
  "timestamp": "2026-03-03T20:08:00Z",
  "exchanges": {
    "CME":    {"status": "open", "session": "ETH", "next": "RTH open 9:30 AM ET", "minutes_until": 808},
    "NYSE":   {"status": "closed", "next": "open 9:30 AM ET", "minutes_until": 808},
    "NASDAQ": {"status": "closed", "next": "open 9:30 AM ET", "minutes_until": 808},
    "LSE":    {"status": "closed", "next": "open 8:00 AM GMT", "minutes_until": 720},
    "EUREX":  {"status": "closed", "next": "open 8:00 AM CET", "minutes_until": 720},
    "TSE":    {"status": "closed", "next": "open 9:00 AM JST", "minutes_until": 780},
    "HKEX":   {"status": "closed", "next": "open 9:30 AM HKT", "minutes_until": 810}
  },
  "volatility": {
    "vix": 18.5,
    "vix9d": 17.2,
    "vix3m": 19.8,
    "vvix": 92.3,
    "term_structure": "contango",
    "vix_percentile_1y": 35
  },
  "regime": {
    "label": "risk_on",
    "confidence": 0.78,
    "crc_score": 62
  },
  "events": {
    "next": {
      "name": "ISM Manufacturing PMI",
      "time": "2026-03-04T15:00:00Z",
      "minutes_until": 1132,
      "impact": "high",
      "consensus": 49.8,
      "previous": 49.2
    },
    "today_remaining": 0,
    "week_high_impact": 5,
    "fomc_days_until": 14,
    "cpi_days_until": 9
  },
  "data_health": {
    "all_fresh": true,
    "stalest": {"source": "naaim_exposure", "age_hours": 72, "expected": "weekly"},
    "degraded": []
  },
  "trust_scores": {
    "curistat_volatility": {"score": 94, "accuracy_30d": 0.78, "uptime_30d": 99.2},
    "alpha_vantage_equities": {"score": 71, "latency_avg_ms": 340, "uptime_30d": 97.1},
    "polygon_market_status": {"score": 88, "latency_avg_ms": 45, "uptime_30d": 99.8}
  },
  "meta": {
    "version": "1.0",
    "cache_age_seconds": 12,
    "next_refresh_seconds": 48
  }
}
```

### What's NOT in v1 (and Why)

- **News sentiment**: Hardest to get right, lowest signal-to-noise, requires expensive NLP or paid feeds. Add in v2 if demand exists.
- **Individual stock data**: This is a macro context endpoint, not a quote service. Agents have their own equity data feeds.
- **Predictions/forecasts**: Those are Curistat's paid product. `/now` is context, not edge.

### Architecture

```
[Cron: every 60s]
  ├── Fetch VIX/VVIX/VIX9D/VIX3M from Yahoo Finance (free)
  ├── Compute exchange status from exchange_calendars (free, local)
  ├── Read economic calendar (already built in Curistat)
  ├── Compute CRC regime (already built in Curistat)
  ├── Read data source health (already built in Curistat)
  └── Write JSON blob to Cloudflare KV store

[Cloudflare Worker]
  └── Serve cached JSON blob on GET /now
      ├── Cache-Control: max-age=30
      ├── ETag support for conditional requests
      └── CORS: allow all (public endpoint)
```

### Serving Cost: $0/month

Cloudflare Workers free tier includes:
- 100,000 requests/day
- 1,000 KV reads/day (but we serve from cache, not KV per-request)
- Cron triggers included

At scale (>100K/day): $5/month for Workers Paid plan (10M requests/month).

---

## Product 2 Spec: OathScore

### What It Scores

For each rated API, OathScore independently tracks and publishes:

| Metric | How Measured | Update Frequency |
|--------|-------------|-----------------|
| **Accuracy** | Compare API claims/forecasts to actual outcomes | Daily |
| **Freshness** | Monitor data staleness (is "real-time" actually real-time?) | Every 5 min |
| **Uptime** | Synthetic monitoring (ping endpoints, measure response) | Every 1 min |
| **Latency** | P50/P95/P99 response times from multiple regions | Every 1 min |
| **Schema stability** | Detect breaking changes in response format | Daily |
| **Documentation quality** | Does the API have OpenAPI spec, llms.txt, examples? | Weekly |
| **Trust signals** | Does it publish accuracy data, sign responses, support verification? | Weekly |

### Composite Score: 0-100

```
Score = weighted average of:
  Accuracy:       35% (the most important thing for agents)
  Uptime:         20%
  Freshness:      15%
  Latency:        15%
  Schema:          5%
  Documentation:   5%
  Trust signals:   5%
```

Accuracy dominates because agents are buying data for decision-making. An API that's up 99.9% but returns garbage data is useless.

### Which APIs to Rate First (v1)

Start with the APIs that trading agents actually use:

**Tier 1 — Financial Data (rate immediately):**

| API | Why | Free Tier Available |
|-----|-----|---------------------|
| Curistat | Our own — proves we hold ourselves to the standard | Yes |
| Alpha Vantage | Only financial MCP server, huge agent user base | Yes (25/day) |
| Polygon.io | Popular for equities/market status | Yes (5/min) |
| Finnhub | Popular free tier, broad coverage | Yes (60/min) |
| Twelve Data | Growing competitor to Alpha Vantage | Yes |
| EODHD | Budget option many agents use | Yes |
| Financial Modeling Prep | Growing, good free tier | Yes |

**Tier 2 — Macro/Economic (rate next):**

| API | Why |
|-----|-----|
| FRED | Economic data (free, public — but freshness varies) |
| Treasury Direct | Auction data (free, public) |
| BLS | Employment/CPI data (free, public) |

**Tier 3 — Infrastructure (rate later):**

| API | Why |
|-----|-----|
| OpenBB | Open-source Bloomberg alt |
| TradingHours.com | Exchange schedule data |
| Benzinga | News/calendar |

### How Accuracy Verification Works

For APIs that make verifiable claims:

1. **Forecast APIs** (like Curistat): Record forecast at time of publication. Compare to actual outcome next day. Track hit rate, MAE, directional accuracy over rolling 30/90/365 day windows.

2. **Real-time quote APIs**: Compare their "real-time" price to a reference source (e.g., CBOE official close). Measure deviation and lag.

3. **Calendar/event APIs**: Did the event happen when they said? Was the consensus value correct? Were surprise events caught?

4. **Market status APIs**: Compare claimed open/close times to actual exchange schedules including holidays and early closes.

For APIs that don't make verifiable claims (just serve historical data): score on freshness, completeness, schema consistency, and uptime only.

### Revenue Model

**Dual-sided:**

| Revenue Stream | Who Pays | Price | Justification |
|---------------|----------|-------|---------------|
| Agent queries | Agents checking scores before purchasing data | $0.002/query (free tier: 50/day) | Low enough agents check habitually |
| Verified badge | APIs wanting "OathScore Verified" certification | $49-199/month | Like a blue checkmark -- proves you welcome scrutiny |
| Detailed reports | Agents wanting full comparison (A vs B vs C) | $0.05/report | Higher value, lower volume |
| Webhook alerts | Agents subscribing to score changes | $9.99/month | "Alert me if my data source degrades" |

**Revenue projections (conservative):**

| Timeline | Agent Queries | Badge Revenue | Reports | Webhooks | Total/Month |
|----------|--------------|---------------|---------|----------|-------------|
| Month 1-3 | $0 (all free tier) | $0 | $0 | $0 | $0 |
| Month 4-6 | $150 | $245 (5 APIs) | $50 | $30 | $475 |
| Month 7-12 | $900 | $990 (10 APIs) | $300 | $100 | $2,290 |
| Year 2 | $4,500 | $4,950 (50 APIs) | $1,500 | $500 | $11,450/mo |

The first 3 months are free -- you're building the historical data that IS the moat. Revenue comes once agents depend on you.

### Architecture

```
[Monitor Service: Railway $5/mo]
  ├── Every 1 min: ping all rated APIs (uptime, latency)
  ├── Every 5 min: check data freshness (compare timestamps)
  ├── Every 1 hour: fetch sample data from forecast APIs
  ├── Every day: compare yesterday's forecasts to actuals (accuracy)
  ├── Every week: check documentation, OpenAPI specs, schema changes
  └── Write all results to Supabase (free tier: 500MB)

[Scoring Engine: Cloudflare Worker]
  ├── Compute composite scores from raw metrics
  ├── Serve /api/score/{api_name} endpoint
  ├── Serve /api/compare?apis=curistat,alphavantage
  └── Cache scores (update every 5 min)

[Public Dashboard: Optional later]
  └── Human-readable version of scores (for API providers, not agents)
```

---

## Combined Product: The Agent's Starting Point

When both products are live, an agent's session looks like:

```
1. GET /now                          → "What's happening?"
2. Read trust_scores in response     → "Who should I trust?"
3. GET /api/score/curistat           → "How reliable is Curistat?"
4. If score > 80: GET curistat/forecast → "What's the forecast?"
5. Trade based on forecast
6. Tomorrow: OathScore compares forecast to actual → score updated
```

**The agent never leaves our ecosystem.** `/now` is the entry point. OathScore is the decision layer. Curistat is the recommended data source. The flywheel spins.

---

## Naming & Branding

### Decision: OathScore

**Domain**: oathscore.ai (confirmed available 2026-03-03)

**Tagline**: *"Every API makes promises. OathScore checks the receipts."*

**Why it works**:
- "Oath" implies accountability — APIs swear their data is accurate
- "Score" tells you exactly what the product does
- Unusual enough to be memorable, clear enough to need no explanation
- Pairs naturally with product language:
  - "Check OathScore before you buy data"
  - "OathScore /now endpoint"
  - "OathScore Verified" badge
  - "What's your OathScore?" (becomes a metric APIs want to improve)

### Relationship to Curistat

Two options:

**Option A — Separate brand:** OathScore is an independent company. Curistat is one of many rated APIs. Maximum credibility ("we rate ourselves too"). Separate domain, separate repo, separate billing.

**Option B — Curistat sub-brand:** OathScore by Curistat. Easier to build (shared infrastructure). Less credible as "independent." APIs may not want to be rated by a competitor.

**Recommendation: Option A.** The independence IS the product. An agent won't trust ratings from a service that also sells competing data. The fact that Curistat submits to OathScore rating (and scores well) becomes a marketing asset for both.

---

## Implementation Plan

### Phase 0: Foundation (Weekend Project)

**Goal**: `/now` endpoint live and serving data.

| # | Task | Who | Time | Cost |
|---|------|-----|------|------|
| 0.1 | Register domain (trustbench.ai or similar) | Owner | 15 min | $12/year |
| 0.2 | Create Cloudflare account (if not existing) | Owner | 10 min | $0 |
| 0.3 | Create GitHub repo (public — this IS the marketing) | Owner | 5 min | $0 |
| 0.4 | Build `/now` endpoint using existing Curistat data pipeline | Claude | 3h | ~$3-5 tokens |
| 0.5 | Deploy to Cloudflare Workers | Claude | 1h | $0 |
| 0.6 | Write README with schema docs, example responses | Claude | 1h | ~$1 tokens |
| 0.7 | Create `llms.txt` for the new domain | Claude | 15 min | ~$0.50 tokens |
| 0.8 | Test with curl / Postman | Owner + Claude | 30 min | $0 |

**Owner total: ~30 min, ~$12**
**Claude total: ~5.5h, ~$5-7 in tokens**
**Infrastructure cost: $0/month**

### Phase 1: Monitoring Infrastructure (Week 1)

**Goal**: OathScore monitoring 7 financial APIs, collecting baseline data.

| # | Task | Who | Time | Cost |
|---|------|-----|------|------|
| 1.1 | Build monitoring service (ping, latency, uptime tracking) | Claude | 4h | ~$4-6 tokens |
| 1.2 | Build accuracy tracker (record forecasts, compare to actuals) | Claude | 3h | ~$3-5 tokens |
| 1.3 | Build freshness checker (data age monitoring) | Claude | 2h | ~$2-3 tokens |
| 1.4 | Deploy monitoring to Railway | Claude | 1h | $5/month |
| 1.5 | Set up Supabase table for metrics storage | Claude | 1h | $0 (free tier) |
| 1.6 | Register for free tiers of all 7 Tier 1 APIs | Owner | 1h | $0 |
| 1.7 | Verify monitoring is collecting data correctly | Owner + Claude | 30 min | $0 |

**Owner total: ~1.5h, $5/month ongoing**
**Claude total: ~11h, ~$10-14 in tokens**

### Phase 2: Scoring Engine (Week 2)

**Goal**: OathScore computing and serving composite scores.

| # | Task | Who | Time | Cost |
|---|------|-----|------|------|
| 2.1 | Build scoring algorithm (weighted composite from raw metrics) | Claude | 3h | ~$3-5 tokens |
| 2.2 | Build `/api/score/{api_name}` endpoint | Claude | 2h | ~$2-3 tokens |
| 2.3 | Build `/api/compare` endpoint (side-by-side) | Claude | 2h | ~$2-3 tokens |
| 2.4 | Integrate trust_scores into `/now` response | Claude | 1h | ~$1 tokens |
| 2.5 | Write API documentation (OpenAPI spec) | Claude | 1h | ~$1 tokens |
| 2.6 | Deploy scoring engine to Cloudflare Workers | Claude | 30 min | $0 |
| 2.7 | Review scores for sanity — do they match reality? | Owner | 1h | $0 |

**Owner total: ~1h, $0**
**Claude total: ~9.5h, ~$9-12 in tokens**

### Phase 3: Distribution (Week 2-3)

**Goal**: Agents can find OathScore.

| # | Task | Who | Time | Cost |
|---|------|-----|------|------|
| 3.1 | Build MCP server for OathScore (FastMCP, 4-5 tools) | Claude | 2h | ~$2-3 tokens |
| 3.2 | Submit to Glama, Smithery, mcpservers.org | Claude | 1h | $0 |
| 3.3 | Submit to awesome-mcp-servers (wong2 + punkpeye) | Claude | 30 min | $0 |
| 3.4 | Submit to Fluora/MonetizedMCP marketplace | Claude | 30 min | $0 |
| 3.5 | Submit to awesome-fintech-api, awesome-quant | Claude | 30 min | $0 |
| 3.6 | Create `/llms.txt` and `/.well-known/ai-plugin.json` | Claude | 30 min | $0 |
| 3.7 | Announce on GitHub (repo README is the announcement) | Claude | 30 min | $0 |
| 3.8 | Review all submissions before they go out | Owner | 30 min | $0 |

**Owner total: ~30 min, $0**
**Claude total: ~5.5h, ~$5-7 in tokens**

### Phase 4: Monetization (Month 2+)

**Goal**: Revenue from both products.

| # | Task | Who | Time | Cost |
|---|------|-----|------|------|
| 4.1 | Add Stripe usage-based billing for `/now` and score queries | Claude | 3h | ~$3-5 tokens |
| 4.2 | Create API key system (free tier + paid tiers) | Claude | 2h | ~$2-3 tokens |
| 4.3 | Set up Stripe account for OathScore (separate from Curistat) | Owner | 30 min | $0 (transaction fees only) |
| 4.4 | Build "Verified" badge system for API providers | Claude | 2h | ~$2-3 tokens |
| 4.5 | Contact Alpha Vantage, Polygon, Finnhub about verified badges | Owner | 2h | $0 |
| 4.6 | Set up webhook alert product | Claude | 2h | ~$2-3 tokens |
| 4.7 | Add x402 payment support (optional, when ready) | Claude | 3h | ~$3-5 tokens |

**Owner total: ~2.5h, transaction fees only**
**Claude total: ~12h, ~$12-19 in tokens**

### Phase 5: Scale & Moat (Month 3-6)

**Goal**: Expand coverage, deepen historical data, become the default.

| # | Task | Who | Time | Cost |
|---|------|-----|------|------|
| 5.1 | Add Tier 2 APIs (FRED, Treasury, BLS — 10 more sources) | Claude | 4h | ~$4-6 tokens |
| 5.2 | Add Tier 3 APIs (news, alternative data — 10 more sources) | Claude | 4h | ~$4-6 tokens |
| 5.3 | Build public dashboard (optional — human-readable scores) | Claude | 6h | ~$6-9 tokens |
| 5.4 | Add global exchange coverage to `/now` (TSE, HKEX, LSE, EUREX) | Claude | 3h | ~$3-5 tokens |
| 5.5 | Add news sentiment to `/now` v2 (if demand exists) | Claude | 4h | ~$4-6 tokens |
| 5.6 | Publish monthly "State of Financial Data APIs" report | Claude | 2h/month | ~$2-3/month tokens |
| 5.7 | Apply for inclusion in AI-Trader benchmark as reference data | Owner | 1h | $0 |

**Owner total: ~1h, $0**
**Claude total: ~23h, ~$23-35 in tokens**

---

## Total Investment Summary

### To MVP (/now + OathScore scoring + distribution): Phases 0-3

| | Owner Time | Owner Cost | Claude Time | Claude Token Cost |
|---|-----------|-----------|-------------|-------------------|
| Phase 0 | 30 min | $12 (domain) | 5.5h | ~$5-7 |
| Phase 1 | 1.5h | $5/mo (Railway) | 11h | ~$10-14 |
| Phase 2 | 1h | $0 | 9.5h | ~$9-12 |
| Phase 3 | 30 min | $0 | 5.5h | ~$5-7 |
| **Total** | **3.5h** | **$12 + $5/mo** | **31.5h** | **~$29-40** |

### To Revenue: Add Phase 4

| | Owner Time | Owner Cost | Claude Time | Claude Token Cost |
|---|-----------|-----------|-------------|-------------------|
| Phase 4 | 2.5h | $0 + Stripe fees | 12h | ~$12-19 |
| **Cumulative** | **6h** | **$12 + $5/mo** | **43.5h** | **~$41-59** |

### To Full Scale: Add Phase 5

| | Owner Time | Owner Cost | Claude Time | Claude Token Cost |
|---|-----------|-----------|-------------|-------------------|
| Phase 5 | 1h | $0 | 23h | ~$23-35 |
| **Cumulative** | **7h** | **$12 + $5/mo** | **66.5h** | **~$64-94** |

### Monthly Operating Costs at Scale

| Item | Cost | Notes |
|------|------|-------|
| Domain | $1/mo ($12/year) | .ai or .io domain |
| Cloudflare Workers | $0-5/mo | Free under 100K/day |
| Railway (monitoring) | $5/mo | Lightweight cron service |
| Supabase | $0/mo | Free tier (500MB, plenty for metrics) |
| API free tier calls | $0/mo | All monitoring uses free tiers |
| **Total** | **$6-11/month** | Until revenue exceeds this |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| APIs block our monitoring | MEDIUM | Lose accuracy data for that API | Use free tiers legitimately; we're a customer, not a scraper |
| Another service launches first | LOW | Lose first-mover | We have 3.5h owner time to MVP. Hard to beat that speed. |
| Agents don't adopt | MEDIUM | No revenue | /now is useful even without OathScore. Build the habit first. |
| Accuracy verification is gamed | LOW | Credibility loss | Multiple verification methods; cross-reference sources; transparency |
| Perceived conflict of interest (Curistat rates itself) | MEDIUM | Credibility | Option A branding: separate entity, rate ourselves same as competitors, publish methodology openly |
| Low API provider interest in badges | MEDIUM | Badge revenue delayed | Agent query revenue stands alone; badges are bonus |

---

## Decision Points for Owner

1. **Domain name**: OathScore.ai? OathScore.io? Something else? Check availability.
2. **Branding**: Confirm separate entity (Option A) vs Curistat sub-brand (Option B). Recommendation: Option A.
3. **Phase 0 timing**: This is a weekend project. When do you want to start?
4. **Scope confirmation**: Build both products (/now + OathScore) or start with just /now?
5. **x402 support**: Defer (like Curistat) or include in Phase 4?

---

## Why This Works

1. **Near-zero barrier to entry**: $12 domain + free infrastructure. The code is a weekend build using components that already exist in Curistat.
2. **Time IS the moat**: Every day of accuracy data collected is a day your competitor can't replicate. Start now, moat grows automatically.
3. **Curistat symbiosis**: /now recommends Curistat. OathScore verifies Curistat. Both drive traffic to the paid product. It's a self-reinforcing ecosystem.
4. **Repository-first**: No website needed. GitHub repo IS the product page. Agents discover through MCP registries and llms.txt, not Google.
5. **The "cat video" hook**: /now is the addictive, low-cost, high-frequency entry point that makes everything else work.

---

*This document requires Owner review and approval before any implementation begins. Per CLAUDE.md Rule 9: no work starts without explicit owner approval.*
