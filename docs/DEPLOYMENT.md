# OathScore Deployment Guide

**Last Updated**: 2026-03-12

## Overview

OathScore runs as a Docker container on Railway, with Cloudflare DNS pointing `api.oathscore.dev` to the Railway service.

## Deploy

```bash
# From repo root
railway up
```

Build takes 1-2 minutes. Railway builds from `Dockerfile` (python:3.12-slim + uvicorn).

## Post-Deploy Checklist

1. `curl https://api.oathscore.dev/health` -- should return `{"status": "ok", ...}`
2. `curl https://api.oathscore.dev/now` -- full world state response
3. `curl https://api.oathscore.dev/scores` -- monitoring scores
4. `curl https://api.oathscore.dev/alerts` -- active alerts
5. Check Railway logs for "Running X probe" messages (all probes should appear)

Fresh deploy starts with empty `data/monitor/` (gitignored). Probes repopulate within minutes. Supabase has persistent history. Scoring requires 10+ pings (~10 min).

## Rollback

Use the Railway dashboard -- it keeps previous deploys. Click "Rollback" on the previous successful deployment.

## Local Development

```bash
uvicorn src.main:app --reload
```

Runs on `http://localhost:8000`. All probes and background tasks start automatically.

## Environment Variables

Set these in Railway service settings:

| Variable | Purpose | Required |
|----------|---------|----------|
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_ANON_KEY` | Supabase anon/public key | Yes |
| `STRIPE_SECRET_KEY` | Stripe live secret key | For billing |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signature secret | For billing |
| `CURISTAT_API_URL` | Curistat backend URL (calendar/forecast data) | Yes |
| `ALPHAVANTAGE_KEY` | Alpha Vantage API key | For monitoring |
| `POLYGON_KEY` | Polygon.io API key | For monitoring |
| `FINNHUB_KEY` | Finnhub API token | For monitoring |
| `TWELVEDATA_KEY` | Twelve Data API key | For monitoring |
| `EODHD_KEY` | EODHD API token | For monitoring |
| `FMP_KEY` | Financial Modeling Prep API key | For monitoring |
| `FRED_KEY` | FRED API key | For monitoring |
| `ALPACA_KEY` | Alpaca API key | For monitoring |
| `ALPACA_SECRET` | Alpaca API secret | For monitoring |
| `TELEGRAM_BOT_TOKEN` | Telegram bot for alerts | For alerts |
| `TELEGRAM_CHAT_ID` | Telegram chat for alerts | For alerts |
| `PORT` | Server port (set by Railway automatically) | Auto |

**Note**: `key_env` values in `src/monitor/config.py` must match these variable names exactly.

## DNS / Domain Setup

- **Domain**: `oathscore.dev` (registered, $12/yr)
- **DNS**: Cloudflare manages DNS
- **`api.oathscore.dev`**: CNAME record pointing to Railway service URL
- **SSL**: Handled automatically by Railway

## Docker

The `Dockerfile` uses:
- Base: `python:3.12-slim`
- Installs from `requirements.txt`
- Runs: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`

The `Procfile` is a fallback: `web: uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}`

## Infrastructure Diagram

```
oathscore.dev (registrar)
     |
     v
Cloudflare (DNS)
     |
     CNAME: api.oathscore.dev -> Railway
     |
     v
Railway (Docker container)
     |
     +-- FastAPI (uvicorn)
     +-- Background probes
     |
     +-- Supabase (PostgreSQL, persistent storage)
     +-- Stripe (billing)
     +-- Telegram (alerts)
```

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md) -- System architecture and data flow
- [REFERENCE_MANUAL.md](REFERENCE_MANUAL.md) -- Section 14 for detailed infrastructure notes
