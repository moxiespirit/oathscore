# State of Financial Data APIs -- March 2026

## How Agent-Ready Is Your Data Provider?

*Published by [OathScore](https://api.oathscore.dev) -- the trust layer for AI trading agents.*

---

AI agents are the fastest-growing consumers of financial data APIs. They need machine-readable docs, predictable auth, stable schemas, and honest rate limits. We audited 11 of the most popular financial data APIs to find out which ones are ready for the agent era -- and which ones are still stuck in 2022.

This is Report #1 in a monthly series. Starting in April, we'll publish full composite quality scores (0-100) based on 30 days of continuous monitoring. This report covers what we found while building the monitoring system.

---

## The 11 APIs We Audited

| API | Category | Free Tier | Paid From |
|-----|----------|-----------|-----------|
| Alpha Vantage | Equities, macro, forex | 25 req/day | $49.99/mo |
| Polygon.io (now Massive) | Market data | 5 req/min | $29/mo |
| Finnhub | Multi-asset, calendar, alt data | 60 req/min | ~$50/mo |
| Twelve Data | Market data, forex, crypto | 8 req/min, 800/day | $29/mo |
| EODHD | Historical data | 20 req/day | EUR 19.99/mo |
| Financial Modeling Prep | Fundamentals, 150+ endpoints | 250 req/day | $19/mo |
| Curistat | Futures volatility forecasting | Developer tiers | $29/mo |
| FRED | Federal Reserve economic data | 120 req/min | Free (all tiers) |
| CoinGecko | Crypto market data, 15K+ coins | 30 req/min (Demo) | $129/mo |
| Alpaca Markets | Stocks, options, crypto trading + data | 200 req/min | $9/mo |
| Yahoo Finance (yfinance) | Equities, options, fundamentals | Unofficial, no key | N/A |

---

## Finding #1: Only 2 Out of 11 Have llms.txt

The `llms.txt` standard lets AI agents understand what an API does without reading HTML documentation. It's the equivalent of a README for machines.

**CoinGecko has it.** Full `llms.txt` and `llms-full.txt` at docs.coingecko.com -- structured context designed specifically for LLM consumption. This is the gold standard.

**Alpaca has it** -- though theirs is more of a curated sitemap pointing to product pages and community forums than a machine-readable API spec.

**The other 9 return 404.** Financial data providers are still largely invisible to AI agents unless someone hard-codes the integration.

---

## Finding #2: MCP Servers Are the New Competitive Moat

MCP (Model Context Protocol) server adoption has been surprisingly strong:

| API | MCP Server | Type | Tools |
|-----|-----------|------|-------|
| CoinGecko | Yes | Official (Beta) | 76+ (hosted endpoint, SSE + HTTP streaming) |
| Alpaca Markets | Yes | Official | 50+ (trading + data in one server) |
| Polygon.io / Massive | Yes | Official | 35+ |
| Financial Modeling Prep | Yes | Official | 250+ |
| Twelve Data | Yes | Official | WebSocket streaming |
| EODHD | Yes | Official | OAuth 2.1 |
| Alpha Vantage | Yes | Official | Full API coverage |
| Finnhub | Yes | Community only | Basic |
| FRED | Yes | Community only | 2+ implementations (3 tools each) |
| Yahoo Finance | Yes | Community only | 5+ wrappers (8-15 tools each) |
| Curistat | No | -- | -- |

**10 out of 11** have MCP servers. CoinGecko leads with 76+ tools and a hosted MCP endpoint that works with Claude Desktop and n8n out of the box. Alpaca's is unique -- it covers both market data queries and order execution through the same interface.

**The takeaway:** MCP is where financial data providers are investing in agent integration. If you're building a trading agent in 2026 and your data provider doesn't have an MCP server, you're doing extra work.

---

## Finding #3: The Agent Discovery Stack Is Mostly Empty

We checked each API for 5 standard discovery files that help agents find and understand services:

| API | OpenAPI | llms.txt | ai-plugin.json | robots.txt | security.txt |
|-----|---------|----------|----------------|------------|-------------|
| CoinGecko | Official (GitHub) | Yes (full) | -- | Yes | -- |
| Alpaca | Official (4 files) | Yes (sitemap) | -- | Yes | -- |
| Polygon / Massive | Community | -- | Yes | Yes | -- |
| Finnhub | Yes (Swagger 2.0) | -- | -- | Yes | -- |
| Alpha Vantage | -- | -- | Yes | -- | -- |
| FRED | Community | -- | -- | Yes | -- |
| Twelve Data | -- | -- | -- | Yes | -- |
| EODHD | -- | -- | -- | Yes (blocks /api/) | -- |
| FMP | Community | -- | -- | 403 (blocked) | -- |
| Yahoo Finance | -- | -- | -- | -- | -- |
| Curistat | -- | -- | -- | -- | -- |

**CoinGecko and Alpaca lead** with 3 out of 5 each. Nobody has all 5, and security.txt adoption is zero across financial data APIs.

**FMP is still concerning** -- it returns 403 Forbidden on nearly all standard paths. **Yahoo Finance has zero discovery infrastructure** because it isn't an official API.

---

## Finding #4: Free Tiers Are Wildly Inconsistent

| API | Rate Limit | Daily/Monthly Cap | Real-Time? | Gotcha |
|-----|-----------|-------------------|------------|--------|
| Alpaca | 200 req/min | No cap | IEX only | SIP data 15-min delayed on free |
| FRED | 120 req/min | No cap | N/A | All 800K+ series free |
| Finnhub | 60 req/min | No daily cap | Yes (slight delay) | Paid pricing not public |
| CoinGecko | 30 req/min | 10,000/month | Yes | Burns through in ~5.5 hours |
| Twelve Data | 8 req/min | 800/day | US equities only | Credit system on paid |
| FMP | 300 req/min (paid) | 250/day | EOD only | 500MB bandwidth cap |
| Alpha Vantage | 5 req/min | 25/day | No | Crippling daily cap |
| EODHD | -- | 20/day | No | 1-year max, demo tickers |
| Yahoo Finance | ~6 req/min | ~950 tickers/session | Yes | Can break without notice |

**FRED is the most generous overall** -- 120 requests/minute with no cap and access to every series. All 800,000+ data points are free because it's a public service of the Federal Reserve.

**Alpaca is the most generous for market data** -- 200 req/min with no daily cap, though the free tier only gets IEX exchange data (not the full consolidated tape).

**CoinGecko's Demo tier** is solid at 30 req/min, but the 10,000 calls/month cap means sustained polling will exhaust it in under 6 hours.

**Yahoo Finance is the riskiest** -- no official API means no guarantees. Yahoo actively tightens anti-scraping measures, and the yfinance library has had recurring outages from crumb rotation and session invalidation.

---

## Finding #5: Auth Is Simple But Not Standardized

| Method | APIs |
|--------|------|
| Header only (most secure) | Alpaca (`APCA-API-KEY-ID` + `APCA-API-SECRET-KEY`) |
| Header recommended | CoinGecko (`x-cg-demo-api-key`), FRED v2 (`Authorization: Bearer`) |
| Header or query param | Polygon, Finnhub, Twelve Data, FMP |
| Query parameter only | Alpha Vantage (`apikey=`), EODHD (`api_token=`), FRED v1 (`api_key=`) |
| No auth / session-based | Yahoo Finance (cookie + crumb), CoinGecko (public tier) |

**For agents, header-based auth is better** -- it keeps keys out of URLs (which get logged, cached, and shared). Alpaca requires it. CoinGecko recommends it. FRED's new v2 API (launched November 2025) switched to it.

No provider uses OAuth for data access. API key in a header is the simplest secure pattern.

---

## Finding #6: The Crypto and Macro Gaps Are Closing

A year ago, crypto and macroeconomic data were underserved by agent-friendly APIs. That's changing fast:

**CoinGecko** now has the most agent-ready crypto API -- official MCP with 76+ tools, llms.txt, OpenAPI spec, and a hosted MCP endpoint. Covers 15,000+ coins plus DEX data via GeckoTerminal across 200+ networks.

**FRED** provides the entire US macroeconomic dataset for free with generous rate limits. The November 2025 v2 API launch added bulk retrieval and header auth. GDP, CPI, yield curves, M2 money supply -- all accessible with a free key.

**Alpaca** bridges trading and data -- its MCP server covers both market data queries and order execution, which is unique. An agent can check a price and place a trade through the same interface.

---

## Finding #7: One API Rebranded and Nobody Noticed

Polygon.io rebranded to **Massive** in October 2025. The old `api.polygon.io` domain still works, but the company is now at `massive.com`. Their MCP server, pricing page, and new features are all under the Massive brand.

If your agent's config says `polygon.io`, it works today but may not forever.

---

## The Agent-Readiness Scorecard

We scored each API on 5 dimensions of agent readiness (not quality -- that comes in April):

| Rank | API | Discovery (5pts) | Auth (5pts) | Free Tier (5pts) | MCP (5pts) | Docs (5pts) | Total (/25) |
|------|-----|-----------|------|-----------|-----|------|-------|
| 1 | **CoinGecko** | 3 | 5 | 4 | 5 | 5 | **22** |
| 2 | **Polygon / Massive** | 3 | 5 | 3 | 5 | 5 | **21** |
| 3 | **Alpaca Markets** | 3 | 5 | 4 | 5 | 4 | **21** |
| 4 | **Finnhub** | 2 | 5 | 5 | 3 | 4 | **19** |
| 5 | **Twelve Data** | 1 | 5 | 4 | 5 | 4 | **19** |
| 6 | **FRED** | 1 | 4 | 5 | 3 | 4 | **17** |
| 7 | **FMP** | 1 | 4 | 4 | 5 | 3 | **17** |
| 8 | **Alpha Vantage** | 1 | 3 | 2 | 4 | 3 | **13** |
| 9 | **EODHD** | 1 | 3 | 1 | 4 | 2 | **11** |
| 10 | **Yahoo Finance** | 0 | 1 | 3 | 2 | 1 | **7** |

**CoinGecko takes the top spot** at 22/25 -- the only API with llms.txt, an official hosted MCP server, header auth, and interactive docs. This is what agent-ready looks like.

**Alpaca and Polygon tie for second** at 21/25. Alpaca's unique advantage is combining data and trading in one MCP server. Polygon has the best documentation.

**FRED scores 17/25** -- held back by discovery (no official OpenAPI or llms.txt) despite having the most generous free tier of any API in this list.

**Yahoo Finance trails at 7/25** -- no official API, no auth system, no discovery, no stability guarantees. It exists because it's free and covers everything, but an agent that depends on it will break.

*Note: Curistat (our own API) is excluded from rankings to avoid self-scoring bias. It will be included in April when composite scores are based on automated monitoring data, not editorial assessment.*

---

## What This Means for Agent Developers

1. **Check for MCP first.** 10 of 11 providers have them. This is the fastest path to integration.
2. **CoinGecko is the model to follow.** llms.txt + hosted MCP + OpenAPI + interactive docs. Other providers should take notes.
3. **Don't trust free tier marketing.** "Free API access" ranges from 200 req/min (Alpaca) to 20 req/day (EODHD).
4. **Use header auth when available.** Keeps keys out of logs. Alpaca requires it, CoinGecko recommends it.
5. **Don't build production on yfinance.** It works until it doesn't, with no warning and no recourse.
6. **Budget for paid tiers.** Most free tiers are demo-grade. An agent making real trading decisions needs Alpaca ($9/mo) or Polygon ($29/mo) at minimum.
7. **Watch for Polygon->Massive migration.** Update configs and documentation references.

---

## Coming in April: Full OathScore Ratings

Starting in April 2026, we'll publish composite quality scores (0-100) for each API based on 30 days of continuous monitoring across 7 dimensions:

| Dimension | Weight | What We Measure |
|-----------|--------|----------------|
| Accuracy | 35% | Forecasts vs actual outcomes (where applicable) |
| Uptime | 20% | Synthetic pings every 60 seconds |
| Freshness | 15% | Actual data age vs claimed |
| Latency | 15% | P50 response times |
| Schema stability | 5% | Breaking response changes |
| Documentation | 5% | OpenAPI, llms.txt, ai-plugin.json, docs access |
| Trust signals | 5% | Published accuracy data, transparency |

Our probes have been running since March 3, 2026 across all 11 APIs. April's report will have real numbers.

---

## About OathScore

OathScore provides two services for AI trading agents:

1. **`/now` Endpoint** -- The current state of the world in one API call: exchange status, VIX/VVIX/term structure, economic event countdowns, data source health. Free, no auth required. [Try it](https://api.oathscore.dev/now).

2. **Quality Ratings** -- Independent, continuous monitoring of 11 financial data APIs. Composite scores (0-100) published monthly starting April 2026.

API: `https://api.oathscore.dev`
GitHub: [github.com/moxiespirit/oathscore](https://github.com/moxiespirit/oathscore)
MCP Server: 8 tools, install via `python -m oathscore_mcp`

---

## Methodology Notes

- Discovery files checked via HTTP GET on March 4, 2026
- MCP servers verified via GitHub repository existence, README, and official documentation
- Free tier limits from official pricing pages as of March 2026
- Auth methods verified from official API documentation
- Agent-readiness scores are editorial assessments, not algorithmic ratings (those come in April)
- Polygon.io/Massive data reflects both domains as they operate in parallel
- Curistat excluded from rankings to avoid self-scoring bias

---

*Next report: April 2026 -- first published OathScore quality ratings with 30 days of monitoring data across all 11 APIs.*

*Questions or corrections? Open an issue on [GitHub](https://github.com/moxiespirit/oathscore/issues).*
