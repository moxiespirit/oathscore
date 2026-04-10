# OathScore Reference Manual

**Version**: 2.0
**Last Updated**: 2026-03-05
**Owner**: moxiespirit
**Classification**: Internal — Operational Reference

> Every API makes promises. OathScore checks the receipts.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Overview](#2-product-overview)
3. [Architecture](#3-architecture)
4. [API Reference](#4-api-reference)
5. [Scoring Methodology](#5-scoring-methodology)
6. [Third-Party Connections](#6-third-party-connections)
7. [Monitoring Infrastructure](#7-monitoring-infrastructure)
8. [Alert & Incident System](#8-alert--incident-system)
9. [Billing & Revenue](#9-billing--revenue)
10. [Launch & Distribution](#10-launch--distribution)
11. [Security & Compliance](#11-security--compliance)
12. [Economic Calendar Reference](#12-economic-calendar-reference)
13. [Exchange Reference](#13-exchange-reference)
14. [Infrastructure & Deployment](#14-infrastructure--deployment)
15. [Development Workflow](#15-development-workflow)
16. [Credentials & Environment](#16-credentials--environment)
17. [Owner Instructions & Rules](#17-owner-instructions--rules)
18. [Roadmap](#18-roadmap)
19. [Troubleshooting / FAQ](#19-troubleshooting--faq)
20. [Decision Log](#20-decision-log)
21. [Project History / Timeline](#21-project-history--timeline)
22. [Document Index](#22-document-index)
Appendix A: [Reusable Template Checklist](#appendix-a-reusable-template-checklist)

---

## 1. Executive Summary

OathScore is an independent trust layer for AI trading agents. It provides three products:

1. **`/now` endpoint** — Real-time world state (exchanges, volatility, economic events, data health) in a single API call. Replaces 4-6 separate API calls that agents currently make.

2. **Quality ratings (0-100)** — Independent, continuous monitoring and scoring of financial data APIs. Agents check OathScore before trusting a data source. APIs seek OathScore verification for credibility.

3. **API audit reports ($299-499)** — Detailed independent analysis of a financial data API's accuracy, reliability, and agent-readiness. See [Section 9.4](#94-audit-report-product).

**Business model**: Freemium SaaS + pay-per-request micropayments. Free tier drives adoption, paid tiers for heavy usage, x402 for agent-native billing.

**Moat**: Historical accuracy data accumulates daily and is unreproducible. A competitor starting later has zero history.

**Status**: Live at https://api.oathscore.dev. Accepting real payments via Stripe. Monitoring 11 financial data APIs.

---

## 2. Product Overview

### 2.1 The Flywheel

```
Agent discovers /now --> uses it daily (habit) --> /now includes OathScore scores
--> agent trusts ratings --> picks highest-rated API --> that API gains users
--> other APIs want OathScore verification --> more APIs rated
--> more agents trust OathScore --> more agents discover /now --> repeat
```

### 2.2 Product 1: `/now` — The Agent's Homepage

A single GET request returns everything an AI trading agent needs to start its session:

- **Exchange status**: 7 global exchanges (CME, NYSE, NASDAQ, LSE, EUREX, TSE, HKEX) with open/close, session type, minutes until next transition
- **Volatility**: VIX, VIX9D, VIX3M, VVIX, SKEW, term structure, 1-year VIX percentile
- **Economic events**: Next event with countdown, FOMC/CPI days until, weekly high-impact count
- **Data health**: Freshness of all upstream sources, degraded source warnings

**Economics**: An agent polling every 60s during a 6.5h trading day = 390 calls/day. 1,000 agents = 390,000 calls/day. At $0.003/call = $35K/month from a cached JSON blob.

### 2.3 Product 2: OathScore — The Credit Bureau for Data APIs

Independent continuous monitoring across 7 dimensions, producing a composite 0-100 score per API. Updated daily after 30-day baseline collection.

**Currently monitoring 11 APIs**: Curistat, Alpha Vantage, Polygon.io, Finnhub, Twelve Data, EODHD, Financial Modeling Prep, FRED, CoinGecko, Alpaca Markets, Yahoo Finance (unofficial).

### 2.4 Product 3: API Audit Reports

Detailed independent audit of a financial data API, delivered as a professional report. See [Section 9.4](#94-audit-report-product) for pricing and template.

### 2.5 Relationship to Curistat

Separate brand, separate repo, separate billing. Curistat is one of many rated APIs. The independence IS the product. OathScore rates Curistat the same as competitors. Both benefit: Curistat gets verified credibility, OathScore gets proven methodology.

Legal entity: Curistat LLC (single entity for both products).

### 2.6 Branding

**Name**: OathScore — "Oath" implies accountability (APIs swear their data is accurate), "Score" tells you exactly what the product does.

**Tagline**: *"Every API makes promises. OathScore checks the receipts."*

**Domain**: oathscore.dev ($12/yr). Chosen over .ai/.io for cost and developer-audience fit.

**Why it works**:
- Unusual enough to be memorable, clear enough to need no explanation
- Natural product language: "Check OathScore before you buy data", "OathScore Verified" badge, "What's your OathScore?"
- Pairs with brand phrases: "The Credit Bureau for Data APIs", "The Trust Layer for AI Agents"

---

## 3. Architecture

### 3.1 System Diagram

```
[Client/Agent]
     |
     v
[api.oathscore.dev] -- Cloudflare DNS --> [Railway] -- FastAPI (Python 3.12, Docker)
     |                                                      |
     |-- /now         <-- aggregator.py <-- exchange_status + volatility + events
     |-- /scores      <-- scoring.py    <-- store.py (local JSON + Supabase)
     |-- /subscribe   <-- billing.py    <-- Stripe API
     |-- /webhooks    <-- main.py       <-- Stripe webhook (HMAC verified)
     |
     v
[Background Tasks -- scheduler.py]
     |-- Ping probe (60s)          --> store.py --> local JSON + Supabase
     |-- Freshness probe (5m)      --> store.py
     |-- Schema probe (1h)         --> store.py
     |-- Accuracy probe (1h)       --> store.py
     |-- Docs probe (24h)          --> store.py
     |-- Daily scores (24h)        --> Supabase daily_scores table
     |-- Alert check (5m)          --> incident_tracker + alert_sender (Telegram)
     |-- Daily digest (24h)        --> alert_sender (Telegram)
```

### 3.2 Technology Stack

| Layer | Technology | Cost |
|-------|-----------|------|
| Language | Python 3.12 | - |
| Framework | FastAPI + uvicorn | - |
| Container | Docker (python:3.12-slim) | - |
| Hosting | Railway | ~$5/mo |
| Database | Supabase (PostgreSQL + REST) | $0 (free tier) |
| Local storage | JSON files in `data/monitor/` | - |
| Billing | Stripe (live mode) | Transaction fees |
| Micropayments | x402 protocol (USDC on Base) | Not yet activated |
| DNS | Cloudflare | $0 |
| Domain | oathscore.dev | $12/yr |
| Alerts | Telegram Bot API | $0 |
| CI | GitHub Actions | $0 |
| MCP | FastMCP (8 tools) | - |

### 3.3 Key Dependencies (requirements.txt)

fastapi, uvicorn, httpx, exchange_calendars, pandas, apscheduler, mcp

### 3.4 Storage Strategy

**Dual-write**: Every probe writes to both local JSON and Supabase. Supabase failure is logged but never blocks local writes. This ensures:
- Local JSON: fast reads, survives Supabase outages
- Supabase: persistent across deploys, queryable, the historical moat

**Local files** (`data/monitor/`, gitignored): pings.json, schemas.json, docs_checks.json, freshness.json, forecast_snapshots.json, active_alerts.json. Max 10,000 entries per file.

**Supabase tables**: pings, schema_snapshots, freshness_checks, docs_checks, forecast_snapshots, daily_scores. All have RLS enabled.

### 3.5 Database Schema

Source: `migrations/001_initial.sql`. All tables in Supabase (PostgreSQL).

#### Table: `pings`
| Column | Type | Notes |
|--------|------|-------|
| id | BIGSERIAL | Primary key |
| api_name | TEXT | NOT NULL |
| endpoint | TEXT | NOT NULL |
| status_code | INT | HTTP status code |
| latency_ms | INT | Response time |
| ok | BOOLEAN | DEFAULT TRUE |
| error | TEXT | Error message if failed |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |

**Index**: `idx_pings_api_time` on (api_name, created_at DESC)

#### Table: `schema_snapshots`
| Column | Type | Notes |
|--------|------|-------|
| id | BIGSERIAL | Primary key |
| api_name | TEXT | NOT NULL |
| endpoint | TEXT | NOT NULL |
| schema_hash | TEXT | SHA-256 of response structure |
| changed | BOOLEAN | DEFAULT FALSE |
| response_schema | JSONB | Full schema snapshot |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |

**Index**: `idx_schemas_api` on (api_name, created_at DESC)

#### Table: `freshness_checks`
| Column | Type | Notes |
|--------|------|-------|
| id | BIGSERIAL | Primary key |
| api_name | TEXT | NOT NULL |
| endpoint | TEXT | NOT NULL |
| data_timestamp | TEXT | Timestamp from API response |
| age_seconds | INT | How old the data is |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |

**Index**: `idx_freshness_api` on (api_name, created_at DESC)

#### Table: `docs_checks`
| Column | Type | Notes |
|--------|------|-------|
| id | BIGSERIAL | Primary key |
| api_name | TEXT | NOT NULL |
| found | TEXT[] | Discovery files found |
| missing | TEXT[] | Discovery files missing |
| docs_accessible | BOOLEAN | DEFAULT FALSE |
| score | FLOAT | Documentation quality score |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |

#### Table: `forecast_snapshots`
| Column | Type | Notes |
|--------|------|-------|
| id | BIGSERIAL | Primary key |
| api_name | TEXT | NOT NULL |
| forecast_date | DATE | Date of forecast |
| forecast_value | FLOAT | Predicted value |
| actual_value | FLOAT | Actual outcome (filled next day) |
| accuracy_score | FLOAT | Computed accuracy |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |

#### Table: `daily_scores`
| Column | Type | Notes |
|--------|------|-------|
| id | BIGSERIAL | Primary key |
| api_name | TEXT | NOT NULL |
| score_date | DATE | NOT NULL |
| composite_score | FLOAT | Weighted composite (0-100) |
| accuracy_score | FLOAT | Accuracy component |
| uptime_score | FLOAT | Uptime component |
| freshness_score | FLOAT | Freshness component |
| latency_score | FLOAT | Latency component |
| schema_score | FLOAT | Schema stability component |
| docs_score | FLOAT | Documentation component |
| trust_score | FLOAT | Trust signals component |
| grade | TEXT | Letter grade (A+, A, B, etc.) |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |

**Index**: `idx_scores_api_date` on (api_name, score_date DESC)
**Constraint**: UNIQUE(api_name, score_date)

#### Row Level Security (RLS)

All 6 tables have RLS enabled:
- **anon role**: SELECT only (public reads)
- **service_role**: INSERT (backend writes)

---

## 4. API Reference

### 4.1 Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/` | GET | None | Landing/agent entry point |
| `/now` | GET | Rate-limited | World state (exchanges, volatility, events, health) |
| `/health` | GET | None | Service health check |
| `/scores` | GET | Rate-limited | All API monitoring scores |
| `/score/{api_name}` | GET | Rate-limited | Individual API quality score (0-100) |
| `/compare?apis=a,b` | GET | Rate-limited | Side-by-side API comparison |
| `/alerts` | GET | None | Active degradation alerts |
| `/status` | GET | None | Full system status + raw metrics |
| `/pricing` | GET | None | Current tier pricing |
| `/subscribe` | POST | None | Create Stripe checkout session |
| `/subscribe/success` | GET | None | Post-checkout landing |
| `/webhooks/stripe` | POST | Stripe HMAC | Stripe webhook receiver |
| `/llms.txt` | GET | None | Agent-readable product description |
| `/llms-full.txt` | GET | None | Complete endpoint documentation |
| `/robots.txt` | GET | None | Agent-aware robots.txt |
| `/ai.txt` | GET | None | AI discovery pointer |
| `/.well-known/ai-plugin.json` | GET | None | ChatGPT plugin manifest |
| `/.well-known/security.txt` | GET | None | Security contact (RFC 9116) |
| `/openapi.json` | GET | None | OpenAPI 3.0.3 spec (auto) |
| `/docs` | GET | None | Interactive Swagger UI |

### 4.2 `/now` Response Schema

```json
{
  "timestamp": "2026-03-03T20:08:00Z",
  "exchanges": {
    "CME": {"status": "open", "session": "ETH", "next": "RTH open 9:30 AM ET", "minutes_until": 808}
  },
  "volatility": {
    "vix": 18.5, "vix9d": 17.2, "vix3m": 19.8, "vvix": 92.3,
    "skew": 135.2, "term_structure": "contango", "vix_percentile_1y": 35
  },
  "events": {
    "next": {"name": "ISM Manufacturing PMI", "time": "...", "minutes_until": 1132, "impact": "high"},
    "today_remaining": 0, "week_high_impact": 5, "fomc_days_until": 14, "cpi_days_until": 9
  },
  "data_health": {"all_fresh": true, "stalest": {"source": "...", "age_hours": 72}, "degraded": []},
  "meta": {"version": "1.0.0", "source": "oathscore.dev", "refresh_interval_seconds": 60}
}
```

**Response headers**: `Cache-Control: public, max-age=30`, `X-Cache-Age-Seconds`, `X-Next-Refresh-Seconds`, `X-RateLimit-Remaining`

### 4.3 Rate Limits

| Tier | /now daily | /score daily | Price |
|------|-----------|-------------|-------|
| Free | 10 | 5 | $0 |
| Founding (first 50) | 5,000 | 2,500 | $9/mo lifetime |
| Pro | 10,000 | 5,000 | $29/mo |
| Enterprise | 100,000 | 50,000 | $99/mo |
| x402 pay-per-request | Unlimited | Unlimited | $0.001-0.005/call |

Free tier tracked by IP. Paid tiers tracked by API key (format: `os_` + 24 hex bytes, hashed with SHA-256).

### 4.4 MCP Server (8 tools)

Run: `python -m oathscore_mcp`

Tools: get_now, get_exchanges, get_volatility, get_events, get_score, compare_apis, get_alerts, check_health

### 4.5 Error Responses

All errors return JSON with an `error` field. Common responses:

**400 Bad Request** — Missing or invalid parameters:
```json
{"error": "Provide ?apis=name1,name2", "available": ["curistat", "alphavantage", "polygon", ...]}
```
Returned by: `/compare` (missing apis param), `/subscribe` (invalid tier), `/webhooks/stripe` (missing signature).

**402 Payment Required** — Rate limit exceeded with x402 enabled:
```json
{"error": "Rate limit exceeded. Pay per request or upgrade.", "upgrade": "https://api.oathscore.dev/pricing"}
```
Includes `PAYMENT-REQUIRED` header with x402 payment instructions. Only returned when x402 is enabled.

**404 Not Found** — Unknown API name:
```json
{"error": "Unknown API: badname", "available": ["curistat", "alphavantage", "polygon", "finnhub", "twelvedata", "eodhd", "fmp", "fred", "coingecko", "alpaca", "yahoo_finance"]}
```
Returned by: `/score/{api_name}`, `/compare` (any unknown name).

**429 Too Many Requests** — Rate limit exceeded (standard):
```json
{"error": "Rate limit exceeded. Free tier: 10/day.", "upgrade": "https://api.oathscore.dev/pricing"}
```
Returned by: `/now`, `/score`, `/compare` when daily limit hit.

**503 Service Unavailable** — Kill switch active or billing misconfigured:
```json
{"error": "Service temporarily unavailable", "reason": "maintenance"}
```
Kill switch: returned for ALL endpoints except `/health`. Billing: returned by `/subscribe` when Stripe not configured.

### 4.6 Quick Start / curl Examples

**Get world state:**
```bash
curl https://api.oathscore.dev/now
```

**Check a specific API's quality score:**
```bash
curl https://api.oathscore.dev/score/curistat
```

**Compare two APIs side-by-side:**
```bash
curl "https://api.oathscore.dev/compare?apis=alphavantage,polygon"
```

**Check active alerts:**
```bash
curl https://api.oathscore.dev/alerts
```

**With API key (paid tier):**
```bash
curl -H "X-API-Key: os_your_key_here" https://api.oathscore.dev/now
# or
curl "https://api.oathscore.dev/now?api_key=os_your_key_here"
```

**Subscribe to a paid tier:**
```bash
curl -X POST https://api.oathscore.dev/subscribe \
  -H "Content-Type: application/json" \
  -d '{"tier": "pro"}'
```
Returns: `{"checkout_url": "https://checkout.stripe.com/...", "api_key": "os_...", "important": "Save your API key NOW."}`

**Python (httpx):**
```python
import httpx
r = httpx.get("https://api.oathscore.dev/now")
data = r.json()
print(f"VIX: {data['volatility']['vix']}")
print(f"CME: {data['exchanges']['CME']['status']}")
```

---

## 5. Scoring Methodology

### 5.1 Composite Score (0-100)

| Component | Weight | What It Measures |
|-----------|--------|-----------------|
| Accuracy | 35% | Does the API return correct data? |
| Uptime | 20% | Is the API available when needed? |
| Freshness | 15% | Is data as current as claimed? |
| Latency | 15% | How fast does it respond? |
| Schema Stability | 5% | Does it break its contract? |
| Documentation | 5% | Can an agent self-integrate? |
| Trust Signals | 5% | Does it welcome scrutiny? |

Missing components are excluded and remaining weights normalized.

### 5.2 Letter Grades

A+ (95-100), A (90-94), B (80-89), C (70-79), D (60-69), F (0-59)

### 5.3 Component Scoring Details

**Accuracy (35%)**:
- Forecast APIs: record prediction, compare to actual next day. Score = 100 * (1 - normalized_error)
- Data APIs: compare values to reference source. Score = correct/total * 100
- Calendar APIs: did events happen when claimed?

**Uptime (20%)**: Last 500 pings. Score = successful_pings / total * 100. Minimum 10 pings required.

**Freshness (15%)**: Average of last 10 checks. Brackets: <60s=100, <300s=90, <900s=75, <3600s=50, <86400s=25, >86400s=0

**Latency (15%)**: Brackets: <200ms=100, <500=80, <1000=60, <2000=40, <5000=20, >5000=0

**Schema (5%)**: Each breaking change in 30 days = -20 points. 0 changes = 100, 5+ = 0.

**Documentation (5%)**: OpenAPI spec (25), llms.txt (25), code examples (20), error docs (15), rate limit docs (15)

**Trust (5%)**: Base 30 + docs quality (25) + publishes forecasts (25) + uptime >=99% (20)

### 5.4 Conflicts of Interest Policy

- Same methodology for all APIs, including our own (Curistat)
- Public methodology (this document)
- Raw data available to paid tiers for independent verification
- Any rated API can dispute their score; disputes and responses are published

---

## 6. Third-Party Connections

Every external service OathScore connects to, why, and how.

### 6.1 Monitored APIs (11)

These are the financial data APIs we actively probe, score, and rate.

| # | API | Base URL | Category | Auth | Free Tier Limit | Key Env Var | Has Forecasts |
|---|-----|----------|----------|------|-----------------|-------------|---------------|
| 1 | **Curistat** | curistat-api-production.up.railway.app | Futures volatility forecasting | None | Unlimited | -- | Yes |
| 2 | **Alpha Vantage** | www.alphavantage.co | Equities, macro, forex | API key | 25 requests/day | `ALPHAVANTAGE_KEY` | No |
| 3 | **Polygon.io** | api.polygon.io | Market data, status | API key | 5/min | `POLYGON_KEY` | No |
| 4 | **Finnhub** | finnhub.io/api/v1 | Multi-asset, calendar | Token | 60/min | `FINNHUB_KEY` | No |
| 5 | **Twelve Data** | api.twelvedata.com | Market data | API key | 800/day | `TWELVEDATA_KEY` | No |
| 6 | **EODHD** | eodhd.com/api | Historical data | API token | 20/day | `EODHD_KEY` | No |
| 7 | **Financial Modeling Prep** | financialmodelingprep.com/api/v3 | Fundamentals | API key | 250/day | `FMP_KEY` | No |
| 8 | **FRED** | api.stlouisfed.org | Macro/economic data | API key | Generous | `FRED_KEY` | No |
| 9 | **CoinGecko** | api.coingecko.com/api/v3 | Crypto market data | None | Rate limited | -- | No |
| 10 | **Alpaca Markets** | data.alpaca.markets | Stocks, options, crypto | Key + Secret | Free with account | `ALPACA_KEY` + `ALPACA_SECRET` | No |
| 11 | **Yahoo Finance** | query1.finance.yahoo.com | Equities, options (unofficial) | None (UA required) | Unofficial | -- | No |

**Endpoints probed per API** (defined in `src/monitor/config.py`):

- **Curistat**: `/health`, `/api/v1/forecast/es`, `/api/v1/calendar/week`
- **Alpha Vantage**: `/query?function=TIME_SERIES_DAILY&symbol=SPY`
- **Polygon.io**: `/v2/aggs/ticker/SPY/prev`
- **Finnhub**: `/quote?symbol=SPY`, `/calendar/economic`
- **Twelve Data**: `/time_series?symbol=SPY&interval=1day`
- **EODHD**: `/real-time/SPY.US`
- **FMP**: `/quote/SPY`
- **FRED**: `/fred/series/observations?series_id=DGS10`
- **CoinGecko**: `/simple/price?ids=bitcoin`, `/coins/bitcoin`
- **Alpaca**: `/v2/stocks/SPY/trades/latest` (header auth)
- **Yahoo Finance**: `/v8/finance/chart/SPY` (User-Agent: OathScore/1.0)

**Documentation URLs** (checked by docs_probe.py):

| API | Docs URL |
|-----|----------|
| Curistat | https://curistat.com |
| Alpha Vantage | https://www.alphavantage.co/documentation/ |
| Polygon.io | https://polygon.io/docs |
| Finnhub | https://finnhub.io/docs/api |
| Twelve Data | https://twelvedata.com/docs |
| EODHD | https://eodhd.com/financial-apis/ |
| FMP | https://site.financialmodelingprep.com/developer/docs |
| FRED | https://fred.stlouisfed.org/docs/api/fred/ |
| CoinGecko | https://docs.coingecko.com/ |
| Alpaca | https://docs.alpaca.markets/ |
| Yahoo Finance | None (unofficial, no public API docs) |

### 6.2 Infrastructure Services

These are services OathScore depends on to operate (not monitored/rated, but used).

| # | Service | Purpose | URL | Auth Method | Cost | Env Vars |
|---|---------|---------|-----|-------------|------|----------|
| 1 | **Railway** | App hosting (Docker) | railway.com | GitHub OAuth | ~$5/mo | `PORT` (auto) |
| 2 | **Supabase** | Persistent database (PostgreSQL + REST) | vehjypmvvanxmzfrwpwa.supabase.co | API key (anon) | $0 (free tier) | `SUPABASE_URL`, `SUPABASE_ANON_KEY` |
| 3 | **Stripe** | Payment processing, subscriptions, webhooks | api.stripe.com | Secret key + webhook HMAC | Transaction fees | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_*` |
| 4 | **Telegram Bot API** | Alert notifications | api.telegram.org | Bot token | $0 | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` |
| 5 | **Yahoo Finance** | Volatility data (VIX, VVIX, VIX9D, VIX3M, SKEW) | query1.finance.yahoo.com | User-Agent header | $0 (unofficial) | -- |
| 6 | **Cloudflare** | DNS (CNAME to Railway) | cloudflare.com | Dashboard | $0 | -- |
| 7 | **GitHub** | Source code, CI/CD, issue tracking | github.com/moxiespirit/oathscore | SSH key | $0 | -- |
| 8 | **GitHub Actions** | Health check CI (every 6h) | github.com (Actions) | GITHUB_TOKEN (auto) | $0 | -- |
| 9 | **x402.org Facilitator** | Micropayment verification/settlement (dormant) | x402.org/facilitator | Payment header | $0 | `X402_FACILITATOR_URL`, `X402_WALLET_ADDRESS` |
| 10 | **exchange_calendars** | Exchange open/close schedule (Python library, local) | N/A (pip package) | N/A | $0 | -- |

### 6.3 Data Flow Summary

```
INBOUND DATA (we consume):
  Yahoo Finance  --> volatility.py    --> /now response (VIX, VVIX, etc.)
  Curistat API   --> events.py        --> /now response (calendar, forecasts)
  exchange_calendars (local) --> exchange_status.py --> /now response (7 exchanges)
  11 monitored APIs --> probe cycle    --> store.py --> local JSON + Supabase

OUTBOUND CONNECTIONS (we send to):
  Supabase       <-- store.py         <-- probe results, daily scores
  Telegram       <-- alert_sender.py  <-- alert notifications
  Stripe         <-- billing.py       <-- checkout sessions, key validation
  x402 Facilitator <-- x402.py        <-- payment verify/settle (dormant)

USER-FACING:
  Agents/Users   --> FastAPI           --> /now, /scores, /score, /compare, etc.
  Stripe         --> /webhooks/stripe  --> subscription lifecycle events
```

### 6.4 Dependency Risk Assessment

| Service | If It Goes Down | Impact | Mitigation |
|---------|----------------|--------|------------|
| Railway | OathScore offline | CRITICAL | Redeploy, or rollback via dashboard |
| Supabase | No persistent writes | LOW | Local JSON continues working, no data loss |
| Stripe | Can't create subscriptions | MEDIUM | Existing keys still work (in-memory) |
| Telegram | No alert delivery | LOW | Alerts logged locally, next cycle retries |
| Yahoo Finance | No volatility in /now | MEDIUM | /now still returns exchanges + events |
| Curistat API | No calendar/forecasts | MEDIUM | Falls back to hardcoded FOMC/CPI dates |
| Any monitored API | That API's probes fail | LOW | Scoring handles missing data by reweighting |
| Cloudflare | DNS resolution fails | CRITICAL | Railway direct URL still works as fallback |
| GitHub | No CI, no code push | LOW | Service continues running independently |

---

## 7. Monitoring Infrastructure

### 7.1 Probe Schedule

| Probe | Interval | File | What It Checks |
|-------|----------|------|----------------|
| Ping | 60s | `ping_probe.py` | HTTP health check, latency |
| Freshness | 5m | `freshness_probe.py` | Data age vs claimed frequency |
| Schema | 1h | `schema_probe.py` | SHA-256 hash of response structure |
| Accuracy snapshot | 1h | `accuracy_probe.py` | Captures forecasts for later verification |
| Accuracy verify | 24h | `accuracy_probe.py` | Compares yesterday's forecast to actual |
| Docs | 24h | `docs_probe.py` | 5 discovery files checked |
| Daily scores | 24h | `scoring.py` | Composite score computation, persisted to Supabase |

All probes run as asyncio tasks in FastAPI lifespan. Each probe is independent -- one failure doesn't affect others.

### 7.2 External Checks

- **GitHub Actions**: Every 6h. Hits /now, /health, /scores. Validates /now schema.
- **Workflow**: `.github/workflows/health-check.yml`

### 7.3 Monitored APIs (11)

See [Section 6.1](#61-monitored-apis-11) for complete details including URLs, endpoints, docs, and auth methods.

### 7.4 Data Retention

- Raw pings: 90 days (10,000 max in local JSON)
- Daily scores: indefinite (Supabase) -- this IS the moat
- Forecast snapshots: indefinite
- Schema snapshots: 1 year

---

## 8. Alert & Incident System

### 8.1 Alert Levels

| Level | Cooldown | Quiet Hours (12-6AM ET) | Delivery |
|-------|----------|------------------------|----------|
| CRITICAL | None | Bypasses | Immediate Telegram |
| URGENT | 1h per source:type | Bypasses | Immediate Telegram |
| WARNING | 4h per source:type | Suppressed | Telegram |
| INFO | 24h (buffered) | N/A | Daily digest |

Higher severity always overrides cooldown.

### 8.2 Alert Thresholds

| Condition | Threshold | Severity |
|-----------|-----------|----------|
| Uptime degraded | <90% (last 60 pings) | WARNING |
| Uptime critical | <50% | URGENT |
| Uptime down | <30% | CRITICAL |
| Consecutive failures | 3+ pings | URGENT |
| Data stale | >2h | WARNING |
| Data stale | >6h | URGENT |
| Data stale | >24h | CRITICAL |
| Schema changed | Hash differs | WARNING |
| High latency | avg >3000ms | WARNING |

### 8.3 Incident Lifecycle

```
Alert detected --> incident_tracker.open_incident() --> alert_sender.send_alert()
                                                              |
                                                        [Telegram]
                                                              |
Next probe cycle --> API recovered? --> incident_tracker.resolve_incident(auto=True)
```

- Active incidents: `data/active_incidents.json`
- History: `data/incident_history.jsonl` (append-only, one JSON line per event)
- Pattern detection: `get_patterns(days=30)` returns APIs with 3+ incidents

### 8.4 Dedup

State in `data/alert_dedup_state.json`. Same source:type within cooldown = suppressed. Escalation (e.g., WARNING -> URGENT) always sends.

### 8.5 Known Failure Scenarios

See `docs/ISSUE_ESCALATION_PLAYBOOK.md` for 10 predetermined scenarios (API-1 through API-10) with specific fixes.

Auto-escalation: 3+ consecutive alert cycles (15 min) at WARNING -> upgrades to URGENT.

---

## 9. Billing & Revenue

### 9.1 Stripe Configuration

- **Mode**: LIVE (real money)
- **Account**: OathScore (under Curistat LLC)
- **Products**: Founding ($9/mo), Pro ($29/mo), Enterprise ($99/mo)
- **Webhook**: checkout.session.completed, customer.subscription.deleted, invoice.payment_failed
- **Webhook URL**: https://api.oathscore.dev/webhooks/stripe
- **Signature verification**: HMAC SHA-256 via `STRIPE_WEBHOOK_SECRET`

### 9.2 API Key System

- Format: `os_` + 24 hex bytes
- Keys hashed with SHA-256 for storage
- In-memory key store (reloaded on deploy)
- Founding slots: max 50, tracked by `_count_tier("founding")`

### 9.3 x402 Micropayments (Dormant)

- Protocol: x402 (USDC on Base network)
- Prices: /now=$0.001, /score=$0.002, /compare=$0.005
- Requires: `X402_ENABLED=true` + `X402_WALLET_ADDRESS` set in Railway
- Currently on testnet (base-sepolia)

### 9.4 Audit Report Product

Independent API audit reports available as a paid service.

- **Price range**: $299 (standard) — $499 (comprehensive)
- **Template**: `docs/sample_audit_report.md`
- **Deliverable**: Detailed report covering accuracy verification, uptime analysis, latency profiling, schema stability, documentation quality, trust signals, and recommendations
- **Status**: Template created, not yet offered to customers (owner rule: need 30 days of monitoring data first)

### 9.5 Revenue Projections

| Timeline | Monthly Revenue |
|----------|----------------|
| Month 1-3 | $0 (free tier, building data moat) |
| Month 4-6 | ~$475 |
| Month 7-12 | ~$2,290 |
| Year 2 | ~$11,450 |

### 9.6 Monthly Operating Costs

| Item | Cost |
|------|------|
| Railway | ~$5 |
| Domain | ~$1 |
| Supabase | $0 (free tier) |
| API free tier calls | $0 |
| **Total** | **~$6/month** |

---

## 10. Launch & Distribution

### 10.1 Launch Status

| Platform | Status | Notes |
|----------|--------|-------|
| Hacker News | **Posted** | Show HN link post to GitHub |
| DEV.to | **Posted** | Full article: "Building the Trust Layer for AI Trading Agents" |
| r/algotrading | Blocked | Account needs 50 subreddit karma |
| r/LocalLLaMA | Blocked | Account needs karma |
| r/ClaudeAI | Blocked | Account needs karma |
| Product Hunt | Skipped | Not a fit for B2D/agent tooling (Decision #10) |
| Twitter/X | Not posted | Draft in docs/reddit_post.txt. Owner has no Twitter account for OathScore. |

### 10.2 MCP Directory Submissions

| Directory | Method | Status | Link |
|-----------|--------|--------|------|
| Glama.ai | Browser form | **Approved & Listed** | Listed |
| mcp.so | GitHub issue | Submitted, waiting | https://github.com/chatmcp/mcpso/issues/668 |
| punkpeye/awesome-mcp-servers | PR | Submitted, waiting | https://github.com/punkpeye/awesome-mcp-servers/pull/2694 |
| mcpservers.org (wong2) | Browser form | Submitted, waiting | -- |
| PulseMCP | Deferred | Auto-ingests from official registry | -- |
| Official MCP Registry | Deferred | Needs npm packaging (`mcp-publisher` CLI required) | -- |

### 10.3 Content Published

- **Monthly Report #1**: "State of Financial Data APIs" (March 2026) — Agent-readiness audit of 7 APIs. Published as `docs/reports/2026-03-state-of-financial-data-apis.md` and DEV.to article.
- **Sample audit report**: Template for $299-499 API audits at `docs/sample_audit_report.md`.
- **4 example agents**: `examples/trading_agent.py`, `examples/market_monitor.py`, `examples/crewai_agent.py`, `examples/langchain_agent.py`.

### 10.4 Reddit Strategy

Owner account (laguia5) has zero karma. All subreddits auto-remove posts. Plan:
1. Build karma organically by commenting in r/algotrading, r/LocalLLaMA
2. Once 50+ karma, post prepared content from `docs/launch_posts.md`
3. Each subreddit has a tailored post already written

---

## 11. Security & Compliance

### 11.1 Kill Switch

Emergency shutdown: write `{"active": true, "reason": "..."}` to `data/kill_switch.json`. All endpoints except `/health` return 503. Middleware in `main.py` checks on every request.

Deactivate: set `{"active": false}` or delete the file. Redeploy or restart.

### 11.2 robots.txt

Agent-aware: 13 training crawlers blocked (GPTBot, CCBot, etc.), 7 discovery bots allowed (Googlebot, Bingbot, etc.). Served from `public/robots.txt`.

### 11.3 security.txt

RFC 9116 compliant. Served at `/.well-known/security.txt`. Contains contact, preferred languages, canonical URL.

### 11.4 Webhook Security

Stripe webhooks verified with HMAC SHA-256 signature using `STRIPE_WEBHOOK_SECRET`. Raw body compared against `Stripe-Signature` header.

### 11.5 Planned Security (Not Yet Implemented)

- Bot detection middleware (UA pattern matching) — Task 5.4
- Webhook rate limiting (per-IP burst + daily budget) — Task 5.5
- Agent reputation scoring (0-100, auto-throttle) — Task 5.6
- Progressive backoff on 429s — Task 5.7
- Response signing (HMAC-SHA256 per agent key) — Task 5.11
- Data fingerprinting (anti-redistribution) — Task 5.12

---

## 12. Economic Calendar Reference

### 12.1 FOMC Meeting Dates

Source: `src/events.py` `FIXED_EVENTS["FOMC"]`. Hardcoded as fallback; live calendar fetched from Curistat API when available.

**2026:**
| Date | Day |
|------|-----|
| 2026-01-28 | Wednesday |
| 2026-03-18 | Wednesday |
| 2026-05-06 | Wednesday |
| 2026-06-17 | Wednesday |
| 2026-07-29 | Wednesday |
| 2026-09-16 | Wednesday |
| 2026-11-04 | Wednesday |
| 2026-12-16 | Wednesday |

**2027 (projected):**
| Date | Day |
|------|-----|
| 2027-01-27 | Wednesday |
| 2027-03-17 | Wednesday |
| 2027-05-05 | Wednesday |
| 2027-06-16 | Wednesday |
| 2027-07-28 | Wednesday |
| 2027-09-22 | Wednesday |
| 2027-11-03 | Wednesday |
| 2027-12-15 | Wednesday |

### 12.2 CPI Release Dates

Source: `src/events.py` `FIXED_EVENTS["CPI"]`. BLS typically releases on the 10th-14th of each month.

**2026:**
Jan 14, Feb 12, Mar 11, Apr 10, May 13, Jun 10, Jul 15, Aug 12, Sep 11, Oct 14, Nov 12, Dec 10

**2027 (projected):**
Jan 13, Feb 10, Mar 10, Apr 14, May 12, Jun 10, Jul 14, Aug 11, Sep 15, Oct 13, Nov 10, Dec 10

### 12.3 March 2026 Scheduled Events

Source: `src/events.py` `SCHEDULED_EVENTS_2026`. Times in ET.

| Date | Time (ET) | Event | Impact |
|------|-----------|-------|--------|
| 2026-03-04 | 10:00 | ISM Services PMI | high |
| 2026-03-04 | 10:00 | Factory Orders | medium |
| 2026-03-05 | 08:15 | ADP Employment Change | high |
| 2026-03-05 | 08:30 | Trade Balance | medium |
| 2026-03-06 | 08:30 | Initial Jobless Claims | medium |
| 2026-03-07 | 08:30 | Nonfarm Payrolls | high |
| 2026-03-07 | 08:30 | Unemployment Rate | high |
| 2026-03-11 | 08:30 | CPI | high |
| 2026-03-12 | 08:30 | PPI | high |
| 2026-03-13 | 08:30 | Initial Jobless Claims | medium |
| 2026-03-14 | 10:00 | Michigan Consumer Sentiment | medium |
| 2026-03-18 | 14:00 | FOMC Rate Decision | high |
| 2026-03-18 | 14:30 | FOMC Press Conference | high |
| 2026-03-20 | 08:30 | Initial Jobless Claims | medium |
| 2026-03-20 | 10:00 | Existing Home Sales | medium |
| 2026-03-25 | 10:00 | Consumer Confidence | medium |
| 2026-03-26 | 08:30 | Durable Goods Orders | medium |
| 2026-03-27 | 08:30 | GDP (Q4 Final) | high |
| 2026-03-27 | 08:30 | Initial Jobless Claims | medium |
| 2026-03-28 | 08:30 | PCE Price Index | high |

### 12.4 How Events Are Served

1. **Primary**: Live calendar fetched from Curistat API (`/api/v1/calendar/week`)
2. **Fallback**: `SCHEDULED_EVENTS_2026` hardcoded list (if Curistat unavailable)
3. **FOMC/CPI countdowns**: Always from `FIXED_EVENTS` (reliable, updated annually)

---

## 13. Exchange Reference

Source: `src/config.py` `EXCHANGES` dict. Used by `src/exchange_status.py` via the `exchange_calendars` Python library.

| Code | Full Name | Calendar Library Name | Timezone | Session Type |
|------|-----------|-----------------------|----------|-------------|
| CME | CME/Globex | `CME` | America/Chicago | Futures (near 24h, 1h maintenance) |
| NYSE | New York Stock Exchange | `NYSE` | America/New_York | Equities (9:30-16:00 ET) |
| NASDAQ | NASDAQ | `NASDAQ` | America/New_York | Equities (9:30-16:00 ET) |
| LSE | London Stock Exchange | `LSE` | Europe/London | Equities (8:00-16:30 GMT) |
| EUREX | EUREX | `XETR` | Europe/Berlin | Derivatives (uses XETR calendar) |
| TSE | Tokyo Stock Exchange | `JPX` | Asia/Tokyo | Equities (9:00-15:00 JST, lunch break) |
| HKEX | Hong Kong Exchange | `HKEX` | Asia/Hong_Kong | Equities (9:30-16:00 HKT, lunch break) |

**Note**: The `exchange_calendars` library handles holidays, early closes, and special sessions automatically. Calendar objects are cached after first creation (expensive to instantiate).

---

## 14. Infrastructure & Deployment

### 14.1 Railway

- **Dashboard**: https://railway.com (GitHub login)
- **Service**: OathScore API
- **Deploy**: `railway up` from repo root
- **Docker**: python:3.12-slim, uvicorn, port from `$PORT`
- **Rollback**: Railway dashboard keeps previous deploys

### 14.2 Deploy Checklist

1. `railway up` from repo root
2. Wait for build + deploy (1-2 min)
3. Verify: `curl https://api.oathscore.dev/health`
4. Verify: `curl https://api.oathscore.dev/now`
5. Verify: `curl https://api.oathscore.dev/scores`
6. Verify: `curl https://api.oathscore.dev/alerts`
7. Check Railway logs for "Running X probe" messages (all 7 probes should appear)

### 14.3 Post-Deploy

Fresh deploy starts with empty `data/monitor/` (gitignored). Probes repopulate within minutes. Supabase has persistent history. Scoring requires 10+ pings (10 min).

### 14.4 Supabase

- **Project URL**: https://vehjypmvvanxmzfrwpwa.supabase.co
- **Tables**: 6 (pings, schema_snapshots, freshness_checks, docs_checks, forecast_snapshots, daily_scores)
- **RLS**: Enabled (anon=SELECT, service_role=INSERT)
- **Free tier**: 500MB, sufficient for monitoring data

### 14.5 GitHub

- **Repo**: https://github.com/moxiespirit/oathscore
- **Topics**: mcp, trading, finance, api, vix, market-data, ai-agents
- **Actions**: health check every 6h

### 14.6 Domain

- **api.oathscore.dev**: CNAME to Railway
- **oathscore.dev**: registered, DNS managed at registrar

---

## 15. Development Workflow

### 15.1 Session Startup

Run `/oathscore-guardian` (or read `docs/START_HERE.md` for manual fallback). This:
1. Checks live date
2. Loads session state + tracker + owner notes
3. Runs zero-trust verification (env vars, URLs, probes, alerts, scoring, calendar, live API)
4. Syncs GitHub issues
5. Presents briefing

### 15.2 Session Save

Run `/session-save` or update `tracking/OATHSCORE_SESSION.md` manually. Include:
- What was done
- What's next (specific enough for a cold start)
- Any owner instructions received

### 15.3 Testing

- **Integration tests**: `tests/test_api.py` (17 tests against live deployment)
- **Local testing**: `uvicorn src.main:app --reload`
- **Test against live**: Always verify after deploy at https://api.oathscore.dev

### 15.4 File Organization

```
oathscore/
  src/                  # All Python source code
    main.py             # FastAPI app, routes, lifespan
    monitor/            # Probes, scoring, alerts, storage
  public/               # Static files (llms.txt, robots.txt, ai-plugin.json)
  examples/             # 4 integration examples
  tests/                # Integration tests
  docs/                 # Business docs, methodology, operational docs, reports
  tracking/             # Session state, task tracker, owner notes
  data/                 # Runtime data (gitignored)
    monitor/            # Probe results (local JSON)
  oathscore_mcp/        # MCP server package
  migrations/           # Supabase SQL
  .claude/skills/       # 3 Claude Code skills
  .github/workflows/    # CI health checks
```

### 15.5 Claude Code Skills

| Skill | Command | Purpose |
|-------|---------|---------|
| oathscore-guardian | `/oathscore-guardian` | Zero-trust session startup + audit + save |
| oathscore-session | `/oathscore-session` | Lightweight session startup/shutdown |
| oathscore-audit | `/oathscore-audit` | Deep forensic codebase audit |

---

## 16. Credentials & Environment

### 16.1 Complete Environment Variable Reference

| Variable | Purpose | Where Set |
|----------|---------|-----------|
| `SUPABASE_URL` | Supabase project URL | Railway |
| `SUPABASE_ANON_KEY` | Supabase public key | Railway |
| `STRIPE_SECRET_KEY` | Stripe API (live) | Railway |
| `STRIPE_WEBHOOK_SECRET` | Webhook signature verification | Railway |
| `STRIPE_PRICE_FOUNDING` | Stripe price ID ($9/mo) | Railway |
| `STRIPE_PRICE_PRO` | Stripe price ID ($29/mo) | Railway |
| `STRIPE_PRICE_ENTERPRISE` | Stripe price ID ($99/mo) | Railway |
| `ALPHAVANTAGE_KEY` | Alpha Vantage monitoring | Railway |
| `POLYGON_KEY` | Polygon.io monitoring | Railway |
| `FINNHUB_KEY` | Finnhub monitoring | Railway |
| `TWELVEDATA_KEY` | Twelve Data monitoring | Railway |
| `EODHD_KEY` | EODHD monitoring | Railway |
| `FMP_KEY` | Financial Modeling Prep monitoring | Railway |
| `FRED_KEY` | FRED economic data monitoring | Railway |
| `ALPACA_KEY` | Alpaca Markets monitoring | Railway |
| `ALPACA_SECRET` | Alpaca Markets monitoring (secret) | Railway |
| `TELEGRAM_BOT_TOKEN` | Alert notifications | Railway |
| `TELEGRAM_CHAT_ID` | Alert notifications | Railway |
| `OATHSCORE_BASE_URL` | API base URL (default: https://api.oathscore.dev) | Optional |
| `CURISTAT_API_URL` | Curistat backend URL | Optional |
| `X402_ENABLED` | Enable micropayments | Not set |
| `X402_WALLET_ADDRESS` | USDC wallet address | Not set |
| `X402_FACILITATOR_URL` | x402 facilitator URL | Not set (default: https://x402.org/facilitator) |
| `X402_NETWORK` | Blockchain network | Not set (default: base-sepolia) |
| `PORT` | Server port | Railway auto |

Total: 25 environment variables (19 set in Railway, 6 optional/not set).

### 16.2 External Service Dashboards

| Service | URL | Login |
|---------|-----|-------|
| Railway | https://railway.com | GitHub |
| Stripe | https://dashboard.stripe.com | Email |
| Supabase | https://supabase.com/dashboard | GitHub |
| GitHub | https://github.com/moxiespirit/oathscore | - |
| Telegram BotFather | https://t.me/BotFather | Telegram |

---

## 17. Owner Instructions & Rules

Source: `tracking/OATHSCORE_SESSION.md` — Owner Instructions section. These are active directives from the owner that carry across sessions.

### 17.1 Active Rules

1. **Revenue is priority** — "no revenue won't work. the goal is to produce income asap"
2. **Keep it simple** — "besides stripe what else is needed for us to just be live. a lot of this is extra"
3. **Don't approach companies for audits yet** — Need 30 days of monitoring data first (sample audit report template exists at `docs/sample_audit_report.md`)
4. **Sponsored comparisons + monthly report = Month 1, not launch** — Don't front-load marketing work
5. **No Twitter account for now** — Not a current priority

### 17.2 Owner Preferences

- Prefers **step-by-step guidance** for external platform navigation (Stripe setup, Reddit posting, etc.)
- When providing copy-paste text, write to a **.txt file** — markdown renders oddly in Claude's output
- Reddit account (laguia5) has zero karma — requires organic karma building before posting

---

## 18. Roadmap

Source: `tracking/PROJECT_TRACKER.md`. Organized by timeline priority.

### 18.1 Deploy Now

| ID | Task | Notes |
|----|------|-------|
| 6.1 | Deploy all pending fixes (alerts, ops docs, guardian) | `railway up` |

### 18.2 This Week

| ID | Task | Notes |
|----|------|-------|
| 5.4 | Bot detection middleware (UA pattern matching) | Block scrapers, allow known bots |
| 5.5 | Webhook rate limiting (per-IP burst + daily budget) | Stripe webhook protection |

### 18.3 Month 1

| ID | Task | Notes |
|----|------|-------|
| 2.5 | Activate x402 (wallet + enable flag) | Owner: set X402_WALLET_ADDRESS + X402_ENABLED in Railway |
| 3.8 | Build Reddit karma | Owner: organic commenting in subreddits |
| 3.9 | Sponsored comparisons (approach APIs) | After 30 days of data |
| 3.11 | Answer SO / GitHub discussions about MCP finance | Ongoing visibility |

### 18.4 When Paying Customers Arrive

| ID | Task | Notes |
|----|------|-------|
| 5.6 | Agent reputation scoring (0-100, auto-throttle) | Port from Curistat |
| 5.7 | Progressive backoff (doubling retry-after on 429s) | Prevents hammering |
| 5.8 | Scraping/abuse pattern detection | Bulk export, rapid sequential |
| 5.9 | Account enforcement escalation (warn -> suspend -> ban) | Port from Curistat |
| 5.10 | Concurrency limits per API key | 2-10 concurrent by tier |

### 18.5 When Scores Publish (~2026-04-03)

| ID | Task | Notes |
|----|------|-------|
| 6.2 | First 30-day scores publish | Requires 30 days of baseline data |
| 5.11 | Response signing (HMAC-SHA256 per agent key) | Integrity verification |
| 5.12 | Data fingerprinting (daily rotating, detect redistribution) | Anti-piracy |
| 5.13 | IP blocklist (permanent + timed) | Port from Curistat |
| 5.14 | Agent admin dashboard (traffic, keys, violations) | Needs website |
| 5.15 | Endpoint cooldowns (cached responses within window) | Reduce compute |

### 18.6 Backlog

| ID | Task | Notes |
|----|------|-------|
| 6.4 | Backup strategy for monitoring data | Supabase is persistent but no backup |
| 6.5 | Structured logging (JSON format for Railway) | Better debugging |

### 18.7 Waiting On

| ID | What | Waiting For |
|----|------|-------------|
| 3.7 | MCP directory approvals | mcp.so #668, punkpeye PR #2694, mcpservers.org |
| 6.2 | First 30-day scores | ~2026-04-03 (30 days from monitoring start) |

---

## 19. Troubleshooting / FAQ

### Q: Why is my score 0 (or no score shown)?

Scores require a minimum of 10 pings (about 10 minutes of monitoring). If the API was just added or the service was recently redeployed, scores will populate shortly. The `/score/{api_name}` endpoint returns `{"status": "monitoring", "message": "Not enough data yet (need 10+ pings)."}` in this case.

### Q: Why is there no accuracy score for most APIs?

Accuracy scoring requires an API that publishes **verifiable forecasts** (predictions that can be checked against actual outcomes). Currently only Curistat has forecasts enabled (`has_forecasts=True`). Other APIs are scored on the remaining 6 dimensions, with weights normalized.

### Q: How do I get an API key?

POST to `/subscribe` with `{"tier": "founding"}` (or "pro" or "enterprise"). You'll get a Stripe checkout URL and your API key immediately. **Save the key** — it's shown once and cannot be recovered.

### Q: My API key stopped working after a redeploy?

API keys are stored in memory and reloaded from Stripe on deploy. If Stripe is unreachable during startup, keys may not load. Check Railway logs for Stripe errors. As a workaround, the key will work again on the next successful deploy.

### Q: Why does `/now` sometimes return stale data?

The `/now` response is cached and refreshed every 60 seconds. The `X-Cache-Age-Seconds` response header tells you how old the cached data is. If it's consistently stale (>120s), check Railway logs for refresh errors.

### Q: How do I activate x402 micropayments?

Set two environment variables in Railway:
1. `X402_ENABLED=true`
2. `X402_WALLET_ADDRESS=<your USDC wallet on Base network>`

Then redeploy. Agents can then pay per request by including a `PAYMENT-SIGNATURE` header.

### Q: What happens if Supabase goes down?

All probe data continues writing to local JSON files in `data/monitor/`. Supabase failures are logged but never block operations. When Supabase recovers, new data resumes writing there. Historical data during the outage exists only in local JSON (lost on redeploy).

### Q: How do I trigger the kill switch?

Write `{"active": true, "reason": "your reason"}` to `data/kill_switch.json` on Railway (via Railway shell or deploy with the file). All endpoints except `/health` will return 503. To deactivate, set `active` to `false` or delete the file.

### Q: Can I add a new API to monitor?

Add its configuration to `src/monitor/config.py` in the `MONITORED_APIS` dict. Include: base URL, endpoints to probe, auth method, key env var. Then add the API key to Railway env vars and redeploy.

### Q: Where are the integration examples?

Four examples in `examples/`:
- `trading_agent.py` — AI trading agent using /now + /score
- `market_monitor.py` — Continuous polling with change alerts
- `crewai_agent.py` — CrewAI integration
- `langchain_agent.py` — LangChain integration

---

## 20. Decision Log

| # | Decision | Rationale | Date |
|---|----------|-----------|------|
| 1 | Separate brand from Curistat | Independence IS the product. Agents won't trust ratings from a competitor. | 2026-03-03 |
| 2 | Railway over Cloudflare Workers | Simpler for background tasks. Workers can't run cron probes easily. | 2026-03-03 |
| 3 | Dual-write storage | Resilience. Supabase failure shouldn't lose probe data. | 2026-03-04 |
| 4 | Free tier tightened (10/day) | Drives upgrades. Original unlimited was too generous. | 2026-03-04 |
| 5 | Founding tier $9/mo lifetime | Creates urgency. First 50 only. | 2026-03-04 |
| 6 | Stripe under Curistat LLC | Single legal entity. Simpler. | 2026-03-04 |
| 7 | Supabase free tier | 500MB is plenty for monitoring metrics. | 2026-03-04 |
| 8 | Telegram only (no SendGrid) | SendGrid has a cost. Telegram is free and instant. | 2026-03-05 |
| 9 | x402 deferred | Needs wallet + enable flag. Focus on Stripe revenue first. | 2026-03-04 |
| 10 | Skip Product Hunt | Not a fit for B2D/agent tooling. | 2026-03-04 |

---

## 21. Project History / Timeline

| Date | Session | Milestone |
|------|---------|-----------|
| 2026-03-03 | S1 | Project created from scratch. Phase 0: `/now` endpoint, agent discovery stack (llms.txt, ai-plugin.json, robots.txt), FastAPI, Docker, Railway deploy. Phase 1: 5 monitoring probes (ping, freshness, schema, accuracy, docs). Phase 2: Scoring engine, `/score`, `/compare`, `/alerts`, MCP server (8 tools). Custom domain `api.oathscore.dev`. 17/17 integration tests. |
| 2026-03-04 | S2 | Supabase persistent storage connected (dual-write). All 6 API provider keys registered in Railway. MCP directory submissions (4 directories, Glama approved). Stripe billing live (real money, 3 tiers). x402 micropayment code deployed (not activated). Launch posts: Hacker News Show HN + DEV.to article. 4 example agents. Webhook HMAC verification. GitHub topics + README star CTA. Free tier tightened to 10/day. Sample audit report template. Monthly report #1. 10 bugs found and fixed (env var mismatch, freshness scoring, trust scoring, daily_scores wiring, FOMC 2027 dates). |
| 2026-03-05 | S3 | Alert system built: `alert_sender.py` (Telegram with dedup, quiet hours, daily digest), `incident_tracker.py` (lifecycle, JSONL history, auto-resolve, pattern detection). Expanded `alerts.py` thresholds. Wired into scheduler. Operational docs: HEALTHCHECK_SCHEDULE.md, ISSUE_ESCALATION_PLAYBOOK.md, ALERT_REGISTRY.md. Owner notes tracking system. Session guardian skill. START_HERE.md quick reference. |

---

## 22. Document Index

| Document | Location | Purpose |
|----------|----------|---------|
| **This manual** | `docs/REFERENCE_MANUAL.md` | Comprehensive reference |
| Quick start | `docs/START_HERE.md` | 20-line orientation for new/crashed sessions |
| Session state | `tracking/OATHSCORE_SESSION.md` | Cumulative state, single source of truth |
| Task tracker | `tracking/PROJECT_TRACKER.md` | All tasks, priorities, status counts |
| Owner notes | `tracking/OWNER_NOTES.md` | Owner<->Claude notification system |
| Business concept | `docs/BUSINESS_CONCEPT.md` | Full business plan, flywheel, projections |
| Methodology | `docs/METHODOLOGY.md` | Public scoring methodology |
| Implementation plan | `docs/IMPLEMENTATION_PLAN.md` | Phase 0-3 build plan with costs |
| Healthcheck schedule | `docs/HEALTHCHECK_SCHEDULE.md` | All probes, intervals, failure handling |
| Escalation playbook | `docs/ISSUE_ESCALATION_PLAYBOOK.md` | Known failures + predetermined fixes |
| Alert registry | `docs/ALERT_REGISTRY.md` | All 9 alert types, channels, dedup |
| Sample audit report | `docs/sample_audit_report.md` | Template for $299-499 API audits |
| MCP registration | `docs/MCP_REGISTRATION.md` | Directory submission status |
| Launch posts | `docs/launch_posts.md` | All launch content + status |
| Monthly report #1 | `docs/reports/2026-03-state-of-financial-data-apis.md` | Agent-readiness audit of 7 APIs |
| Project rules | `CLAUDE.md` | Claude Code project instructions |
| README | `README.md` | Public-facing GitHub README |
| Supabase schema | `migrations/001_initial.sql` | 6 tables + RLS |

---

## Appendix A: Reusable Template Checklist

When starting a new project, create these documents in order:

1. **CLAUDE.md** — Project rules for Claude Code (architecture, directories, env vars, rules)
2. **tracking/SESSION_STATE.md** — Cumulative state file (endpoints, file map, credentials, decisions)
3. **tracking/PROJECT_TRACKER.md** — Task list with initiatives, priorities, status
4. **tracking/OWNER_NOTES.md** — Owner<->Claude notification system
5. **docs/START_HERE.md** — Quick reference (20 lines, read order)
6. **docs/BUSINESS_CONCEPT.md** — Business plan, revenue model, moat
7. **docs/METHODOLOGY.md** — How the core product works (public-facing)
8. **.claude/skills/project-guardian/skill.md** — Session guardian skill
9. **docs/HEALTHCHECK_SCHEDULE.md** — What runs, when, failure handling
10. **docs/ISSUE_ESCALATION_PLAYBOOK.md** — Known failures + fixes
11. **docs/ALERT_REGISTRY.md** — All alert types, channels, dedup
12. **docs/REFERENCE_MANUAL.md** — This document (consolidates everything)

---

*This is a living document. Update after significant changes.*
