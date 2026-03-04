# OathScore Launch Posts

## Launch Status (2026-03-04)

| Platform | Status | Notes |
|----------|--------|-------|
| r/algotrading | Blocked | Account needs 50 karma |
| r/LocalLLaMA | Blocked | Account needs karma |
| r/ClaudeAI | Blocked | Account needs karma |
| Hacker News | Posted | Show HN link post |
| DEV.to | Posted | Full article |
| Product Hunt | Skipped | Not a fit |

## Reddit: r/algotrading

**Title**: I built an independent quality rating system for financial data APIs — like a credit bureau for data sources

**Body**:

I've been building AI trading agents and got frustrated by the lack of transparency around data API quality. Is Alpha Vantage actually reliable? Is Polygon's "real-time" data actually real-time? How often does Finnhub go down?

So I built **OathScore** — an independent monitoring system that continuously rates financial data APIs on accuracy, uptime, freshness, latency, schema stability, and documentation quality. Think of it as a credit score for data APIs.

**Two products:**

1. **`/now` endpoint** — Returns the current state of the world in one call: which exchanges are open, VIX/VVIX/SKEW levels, term structure, upcoming economic events, FOMC/CPI countdowns. Replaces 4-6 separate API calls.

2. **Quality ratings** — Independent 0-100 composite scores for 7 financial data APIs (Alpha Vantage, Polygon, Finnhub, Twelve Data, EODHD, FMP, Curistat). Scores based on 30 days of continuous monitoring.

Currently monitoring and collecting baseline data. Scores populate after 30 days.

**For AI agents**: Full MCP server with 8 tools, so Claude/GPT/CrewAI agents can check data quality before committing to a source.

**Pricing**: 10 free calls/day, paid tiers from $9/mo, or pay-per-request with USDC via x402 protocol.

Live: https://api.oathscore.dev/now
GitHub: https://github.com/moxiespirit/oathscore

Would love feedback from this community. What APIs would you want rated? What metrics matter most to you?

---

## Reddit: r/LocalLLaMA

**Title**: Built an MCP server that gives trading agents real-time world state in one call

**Body**:

If you're building AI agents that interact with financial markets, you probably know the pain of assembling market context from multiple APIs. "Are markets open? What's VIX? Any FOMC coming up?"

I built **OathScore** — an MCP server with 8 tools:

- `get_now` — Full world state: 7 exchange statuses, VIX/VVIX/SKEW/term structure, economic events, data health
- `get_score` — Independent quality rating (0-100) for any financial data API
- `compare_apis` — Side-by-side comparison of data sources
- `get_alerts` — Active degradation alerts

One call to `get_now` replaces 4-6 separate API calls. Your agent gets everything it needs to make informed decisions.

**Install:**
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

Free tier: 10 calls/day. Also supports x402 micropayments (pay per request with USDC, no signup).

GitHub: https://github.com/moxiespirit/oathscore
Live API: https://api.oathscore.dev

---

## Reddit: r/MCP (if exists) or r/ClaudeAI

**Title**: OathScore MCP Server — real-time market data + API quality ratings for trading agents

**Body**:

Sharing an MCP server I built for AI agents that need financial market context:

**8 tools:**
- `get_now` — Exchange status (CME, NYSE, NASDAQ, LSE, EUREX, TSE, HKEX), volatility (VIX, VVIX, SKEW, term structure), economic events, data health
- `get_exchanges` / `get_volatility` / `get_events` — Focused subsets
- `get_score` / `compare_apis` — Independent quality ratings for 7 financial data APIs
- `get_alerts` / `check_health` — Monitoring

The quality rating piece is unique — it's like a credit bureau for data APIs. Continuously monitors accuracy, uptime, freshness, latency for Alpha Vantage, Polygon, Finnhub, Twelve Data, EODHD, FMP, and Curistat.

Works with Claude Desktop, Claude Code, Cursor, or any MCP-compatible client.

GitHub: https://github.com/moxiespirit/oathscore

---

## Hacker News: Show HN

**Title**: Show HN: OathScore – Independent quality ratings for financial data APIs

**URL**: https://github.com/moxiespirit/oathscore

**Text** (if self-post):

OathScore is the credit bureau for financial data APIs. We continuously monitor accuracy, uptime, freshness, latency, and schema stability of APIs like Alpha Vantage, Polygon, Finnhub, and others, producing a composite 0-100 quality score.

Two products:

1. /now endpoint — current world state for trading agents (exchange status, VIX/VVIX/SKEW, economic events) in a single call

2. Quality ratings — independent, transparent scores published with full methodology

Built for AI trading agents. MCP server with 8 tools. Also supports x402 micropayments for pay-per-request access.

Live: https://api.oathscore.dev/now

---

## DEV.to Article Outline

**Title**: Building the Trust Layer for AI Trading Agents

**Sections**:

1. The Problem: AI agents blindly trust their data sources
2. The Insight: Agents need a "credit bureau" for APIs
3. Building OathScore: Architecture decisions
   - Why /now replaces 6 API calls
   - The scoring methodology (weighted composite)
   - MCP server for native agent integration
4. x402: Pay-per-request micropayments for agents
5. What We Monitor (and why accuracy is weighted 35%)
6. Results so far
7. What's next: 30+ APIs, historical data, the trust layer thesis
