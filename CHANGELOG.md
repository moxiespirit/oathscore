# Changelog

All notable changes to OathScore are documented here.

## 2026-03-05

### Added
- Alert system with degradation detection, incident tracking, and Telegram notifications
- Operational docs: ALERT_REGISTRY.md, HEALTHCHECK_SCHEDULE.md, ISSUE_ESCALATION_PLAYBOOK.md
- `oathscore-guardian` skill for zero-trust session startup audits
- `oathscore-audit` skill for comprehensive forensic verification
- `oathscore-session` skill for session startup

## 2026-03-04

### Added
- Example agents: httpx, CrewAI, LangChain, AutoGen integration examples
- Launch post drafts for Reddit, Hacker News, Twitter
- Sample API audit report template ($299-499 product)
- x402 micropayment support (USDC on Base) for pay-per-request billing
- Stripe billing system with tiered subscriptions (Founding $9/mo, Pro $29/mo, Enterprise $99/mo)
- API key support (`X-API-Key` header or `?api_key=` query param)

### Changed
- Tightened free tier: 10/day `/now`, 5/day `/score`
- Updated README with pricing tiers and audit services

## 2026-03-03

### Added
- Supabase persistent storage with SQL migration (6 tables, RLS enabled)
- Test suite: 17 integration tests against live deployment
- Custom domain live at `api.oathscore.dev` (Cloudflare DNS -> Railway)
- `/alerts` endpoint and alerts MCP tool for degradation detection
- GitHub Actions health check workflow (every 6h)
- Rate limiting (tiered by IP and API key)
- Accuracy probes and forecast verification
- `/status` endpoint with full system metrics
- Freshness probe, `/compare` endpoint
- Scoring engine: 7-component weighted composite (0-100)
- 7 MCP tools (get_now, get_exchanges, get_volatility, get_events, get_score, compare_apis, get_alerts)

## 2026-03-02

### Added
- Phase 1: Monitoring probes (ping, schema, docs) + `/scores` endpoint
- Root `/` endpoint with agent entry point
- MCP server with 5 initial tools
- Rich economic event calendar with hardcoded March 2026 fallback
- `robots.txt` with 16 blocked training crawlers + discovery bot allowlist
- Agent discovery files: `llms.txt`, `llms-full.txt`, `ai.txt`, `ai-plugin.json`

### Fixed
- Exchange status: tz-aware timestamp comparisons
- EUREX calendar (XETR -> correct identifier)
- Dockerfile PORT variable for Railway

## 2026-03-01

### Added
- Initial project: business concept, implementation plan, methodology, README
- Phase 0: `/now` endpoint with exchange status, volatility, economic events, data health
- Domain registered: `oathscore.dev`
