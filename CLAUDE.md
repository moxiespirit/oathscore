# OathScore - Claude Code Instructions

## Project Overview
OathScore is a trust layer for AI trading agents. Two products:
1. `/now` endpoint — real-time world state (exchanges, volatility, events, data health) in one call
2. API quality ratings — independent scoring of financial data APIs (0-100 composite)

## Architecture
- **Backend**: FastAPI on Railway (Docker), Python 3.12+
- **Frontend/Docs**: Static files served from `public/`
- **Storage**: Dual-write — local JSON (`data/monitor/`) + Supabase (persistent)
- **Billing**: Stripe (webhooks verified with HMAC SHA-256) + x402 micropayments (USDC)
- **Domain**: `api.oathscore.dev` (Cloudflare DNS -> Railway)

## Key Directories
```
src/                    # All Python source
  main.py               # FastAPI app, all routes
  aggregator.py          # Builds /now response
  events.py              # Economic calendar + FOMC/CPI countdowns
  exchange_status.py     # Exchange open/close logic
  volatility.py          # VIX/VVIX/term structure
  billing.py             # Stripe + API key management
  rate_limit.py          # Tiered rate limiting
  x402.py                # Pay-per-request micropayments
  config.py              # Shared constants
  mcp_server.py          # MCP server (8 tools)
  monitor/
    scheduler.py         # Background probe loops
    ping_probe.py        # Uptime + latency
    freshness_probe.py   # Data staleness
    schema_probe.py      # Schema stability
    docs_probe.py        # Documentation quality
    accuracy_probe.py    # Forecast verification
    scoring.py           # Composite score engine
    alerts.py            # Degradation detection
    store.py             # Local JSON + Supabase dual-write
    supabase_store.py    # Supabase REST client
    config.py            # Monitored API definitions
public/                 # Static files (llms.txt, ai-plugin.json, robots.txt)
examples/               # Integration examples (httpx, CrewAI, LangChain)
tests/                  # API tests against live deployment
docs/                   # Methodology, launch posts
tracking/               # Session state, task tracking
```

## Environment Variables (Railway)
- `SUPABASE_URL`, `SUPABASE_ANON_KEY` — Supabase connection
- `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` — Stripe billing
- `CURISTAT_API_URL` — Curistat backend for calendar/forecast data
- `ALPHAVANTAGE_KEY`, `POLYGON_KEY`, `FINNHUB_KEY`, `TWELVEDATA_KEY`, `EODHD_KEY`, `FMP_KEY` — Monitored API keys

## Session State
Read `tracking/OATHSCORE_SESSION.md` first in every session. It has complete state: all endpoints, credentials, bugs, decisions, and task status.

## Rules
1. **Test against live**: `https://api.oathscore.dev` — always verify after deploy
2. **Dual-write**: Every store operation writes local JSON AND Supabase
3. **Env var names must match Railway**: Check `src/monitor/config.py` `key_env` values
4. **Deploy**: `railway up` from repo root (Docker build)
5. **Don't break /now**: It's the core product. Always test after changes.
