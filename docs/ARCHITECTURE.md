# OathScore Architecture

**Last Updated**: 2026-03-12

## System Overview

OathScore is a pure FastAPI backend deployed on Railway. No frontend -- all responses are JSON or plain text. Agents consume the API directly.

```
                         +-----------------+
                         |  AI Agents /    |
                         |  HTTP Clients   |
                         +--------+--------+
                                  |
                                  v
                    +-------------+-------------+
                    | api.oathscore.dev         |
                    | Cloudflare DNS (CNAME)    |
                    +-------------+-------------+
                                  |
                                  v
              +-------------------+-------------------+
              |          Railway (Docker)              |
              |    python:3.12-slim + uvicorn          |
              |                                        |
              |  +----------------------------------+  |
              |  |  FastAPI App (src/main.py)       |  |
              |  |                                  |  |
              |  |  Middleware:                      |  |
              |  |    - Kill switch (503 override)   |  |
              |  |    - Bot detection (403 crawlers) |  |
              |  |    - CORS (allow_origins=["*"])   |  |
              |  |    - Anti-training headers        |  |
              |  |                                  |  |
              |  |  Routes:                         |  |
              |  |    /now     <- aggregator.py     |  |
              |  |    /scores  <- scoring.py        |  |
              |  |    /score/  <- scoring.py        |  |
              |  |    /alerts  <- alerts.py         |  |
              |  |    /status  <- scoring + store   |  |
              |  |    /pricing <- billing.py        |  |
              |  |    /subscribe <- billing.py      |  |
              |  +----------------------------------+  |
              |                                        |
              |  +----------------------------------+  |
              |  |  Background Tasks (scheduler.py) |  |
              |  |    Ping probe       (60s)        |  |
              |  |    Freshness probe  (5m)         |  |
              |  |    Alert check      (5m)         |  |
              |  |    Schema probe     (1h)         |  |
              |  |    Accuracy probe   (1h)         |  |
              |  |    Docs probe       (24h)        |  |
              |  |    Daily scores     (24h)        |  |
              |  |    Daily digest     (24h)        |  |
              |  +----------------------------------+  |
              +-------------------+-------------------+
                                  |
                    +-------------+-------------+
                    |                           |
              +-----v-----+             +------v------+
              | Local JSON |             |  Supabase   |
              | data/      |             | (PostgreSQL)|
              | monitor/   |             | 6 tables    |
              +------------+             | RLS enabled |
                                         +------+------+
                                                |
                                         +------v------+
                                         |   Stripe    |
                                         | (Billing)   |
                                         +-------------+
```

## Component Map

| Module | Purpose |
|--------|---------|
| `src/main.py` | FastAPI app, all routes, middleware (request logging, bot detection, anti-training headers, kill switch), lifespan |
| `src/aggregator.py` | Builds `/now` response from sub-modules |
| `src/exchange_status.py` | Exchange open/close logic (7 global exchanges) |
| `src/volatility.py` | VIX/VVIX/term structure from Curistat |
| `src/events.py` | Economic calendar + FOMC/CPI countdowns |
| `src/billing.py` | Stripe checkout, API key management, tier logic |
| `src/rate_limit.py` | Tiered rate limiting (IP + API key) |
| `src/x402.py` | Pay-per-request micropayments (USDC on Base) |
| `src/config.py` | Shared constants (refresh interval, etc.) |
| `src/mcp_server.py` | MCP server with 8 tools for AI agent integration |
| `src/monitor/scheduler.py` | Background probe loop orchestration |
| `src/monitor/ping_probe.py` | Uptime + latency measurement |
| `src/monitor/freshness_probe.py` | Data staleness detection |
| `src/monitor/schema_probe.py` | Schema stability tracking |
| `src/monitor/accuracy_probe.py` | Forecast verification |
| `src/monitor/docs_probe.py` | Documentation quality assessment |
| `src/monitor/scoring.py` | 7-component weighted composite score engine |
| `src/monitor/alerts.py` | Degradation detection logic |
| `src/monitor/alert_sender.py` | Telegram alert delivery |
| `src/monitor/incident_tracker.py` | Incident lifecycle tracking |
| `src/monitor/store.py` | Local JSON + Supabase dual-write |
| `src/monitor/supabase_store.py` | Supabase REST client |
| `src/monitor/config.py` | Monitored API definitions (11 APIs) |

## Middleware Stack

Middleware executes in this order on each request (FastAPI LIFO registration):

1. **Kill switch** -- Returns 503 for all routes except `/health` when active
2. **Bot detection** -- 403 for training crawlers, allows discovery bots, always allows `/health` + `/robots.txt` + `/llms.txt` + `/ai.txt`
3. **Anti-training headers** -- Adds `X-Robots-Tag: noai, noimageai` and `X-AI-Training: disallow` to all responses
4. **Request logging** -- Logs every request: method, path, status code, latency (ms), User-Agent, IP. Format: `REQ GET /now 200 12ms ua=... ip=...`. Enables traffic analysis for bot detection tuning, agent funnel measurement, and discovery bot effectiveness.
5. **CORS** -- `allow_origins=["*"]` (intentional for public API)

## Data Flow

### `/now` Request Flow

```
Client GET /now
  -> Rate limit check (IP or API key)
  -> Return cached response (refreshed every 60s in background)

Background refresh (every 60s):
  aggregator.build_now_response()
    -> exchange_status.get_all_statuses()    (7 exchanges)
    -> volatility.get_volatility()           (VIX/VVIX from Curistat)
    -> events.get_next_events()              (economic calendar)
    -> store.check_data_health()             (source freshness)
  -> Cache result in memory
```

### Probe Cycle

```
scheduler.py starts all probes as asyncio tasks on app startup

Each probe:
  1. HTTP request to target API endpoint
  2. Extract metrics (latency, status, data timestamp, schema hash, etc.)
  3. Dual-write: local JSON (data/monitor/*.json) + Supabase table
  4. Alert check: compare metrics against thresholds
  5. If degraded: create incident, send Telegram alert
```

### Scoring Pipeline

```
scoring.compute_score(api_name):
  1. Read last 500 pings -> uptime % and avg latency
  2. Read last 10 freshness checks -> avg staleness
  3. Read schema changes in 30 days -> stability score
  4. Read docs check -> documentation score
  5. Read forecast accuracy -> accuracy score
  6. Compute trust signals
  7. Weighted average (35% accuracy, 20% uptime, 15% freshness,
     15% latency, 5% schema, 5% docs, 5% trust)
  8. Letter grade assignment (A+ through F)
```

## Infrastructure

| Component | Service | Cost |
|-----------|---------|------|
| Hosting | Railway (Docker) | ~$5/mo |
| Database | Supabase PostgreSQL (free tier) | $0 |
| DNS | Cloudflare | $0 |
| Domain | oathscore.dev | $12/yr |
| Billing | Stripe | Transaction fees |
| Alerts | Telegram Bot API | $0 |
| CI | GitHub Actions (health check every 6h) | $0 |

## Storage Strategy

**Dual-write** to both local JSON and Supabase on every probe:
- **Local JSON** (`data/monitor/`, gitignored): Fast reads, survives Supabase outages. Max 10,000 entries per file.
- **Supabase**: Persistent across deploys, queryable, historical moat. 6 tables with RLS (anon=SELECT, service_role=INSERT).

Supabase failure is logged but never blocks local writes.

## See Also

- [REFERENCE_MANUAL.md](REFERENCE_MANUAL.md) -- Full operational reference (sections 3, 5, 14)
- [METHODOLOGY.md](METHODOLOGY.md) -- Scoring methodology details
- [DEPLOYMENT.md](DEPLOYMENT.md) -- Deploy procedures and env vars
