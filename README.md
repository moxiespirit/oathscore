# OathScore

> Every API makes promises. OathScore checks the receipts.

**The trust layer for AI agents.** Two products:

1. **`/now`** — A single endpoint returning the current state of the world for trading agents. Exchange status, volatility, events, regime, data health — one call.
2. **OathScore Ratings** — Independent, continuous verification of data API accuracy, uptime, freshness, and reliability. The credit bureau for data APIs.

## For AI Agents

```bash
# What's happening right now?
curl https://api.oathscore.dev/now

# Should I trust this data source?
curl https://api.oathscore.dev/score/curistat

# Compare two sources
curl https://api.oathscore.dev/compare?apis=curistat,alphavantage
```

## For MCP-Compatible Agents (Claude Code, Cursor, etc.)

```json
{
  "mcpServers": {
    "oathscore": {
      "command": "python",
      "args": ["-m", "oathscore_mcp"]
    }
  }
}
```

Requires: `pip install httpx mcp[cli]` and clone this repo.

## MCP Tools

| Tool | Description |
|------|-------------|
| `get_now` | Current world state: exchanges, volatility, events, data health |
| `get_exchanges` | Open/close status for 7 exchanges with next transition times |
| `get_volatility` | VIX, VIX9D, VIX3M, VVIX, SKEW, term structure |
| `get_events` | Next event, FOMC/CPI countdowns, week high-impact count |
| `get_score` | OathScore rating for a specific API (0-100 composite + grade) |
| `compare_apis` | Side-by-side comparison of two or more data APIs |
| `check_health` | Service health and data freshness |

## What OathScore Monitors

For each rated API:

| Metric | Weight | How Measured |
|--------|--------|-------------|
| Accuracy | 35% | Compare forecasts/claims to actual outcomes daily |
| Uptime | 20% | Synthetic monitoring every 60 seconds |
| Freshness | 15% | Is "real-time" actually real-time? |
| Latency | 15% | P50/P95/P99 from multiple regions |
| Schema stability | 5% | Detect breaking changes |
| Documentation | 5% | OpenAPI spec, llms.txt, examples |
| Trust signals | 5% | Published accuracy data, response signing |

## Rated APIs (v1)

| API | Category | Score | Status |
|-----|----------|-------|--------|
| Curistat | Futures volatility | -- | Monitoring |
| Alpha Vantage | Equities/macro | -- | Monitoring |
| Polygon.io | Market data | -- | Monitoring |
| Finnhub | Multi-asset | -- | Monitoring |
| Twelve Data | Market data | -- | Monitoring |
| EODHD | Historical data | -- | Monitoring |
| Financial Modeling Prep | Fundamentals | -- | Monitoring |

Scores populate after 30 days of monitoring data.

## Machine-Readable Discovery

- [`/llms.txt`](https://oathscore.dev/llms.txt) — Agent-readable product description
- [`/llms-full.txt`](https://oathscore.dev/llms-full.txt) — Complete endpoint documentation
- [`/.well-known/ai-plugin.json`](https://oathscore.dev/.well-known/ai-plugin.json) — ChatGPT plugin manifest
- [`/api/discover`](https://api.oathscore.dev/discover) — OpenAPI 3.0.3 spec

## Pricing

| Tier | `/now` Calls | Score Queries | Price |
|------|-------------|---------------|-------|
| Free | 100/day | 50/day | $0 |
| Pro | 10,000/day | 5,000/day | $29/mo |
| Enterprise | 100,000/day | 50,000/day | $99/mo |
| API Provider Badge | N/A | N/A | $49-199/mo |

## Architecture

```
[Monitoring Service - Railway $5/mo]
  Every 60s: ping all rated APIs (uptime, latency)
  Every 5m: check data freshness
  Every 1h: record forecast snapshots
  Every 24h: compare forecasts to actuals (accuracy)
  Store: Supabase (free tier)

[/now Endpoint - Cloudflare Workers $0/mo]
  Every 60s: fetch VIX, compute exchange status, read events
  Serve: cached JSON, max-age=30, ETag support

[Scoring Engine - Cloudflare Workers $0/mo]
  Every 5m: recompute composite scores from raw metrics
  Serve: /score, /compare, /alerts endpoints
```

## License

Proprietary. All rights reserved.
