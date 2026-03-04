# OathScore Project Tracker

**Last Updated**: 2026-03-04
**Owner**: moxiespirit
**Repo**: https://github.com/moxiespirit/oathscore

---

## Initiative 1: Core Product (COMPLETE)

| ID | Task | Owner | Status | Date | Notes |
|----|------|-------|--------|------|-------|
| 1.1 | /now endpoint + agent discovery stack | Claude | DONE | 2026-03-03 | Phase 0 |
| 1.2 | Monitoring probes (ping, freshness, schema, accuracy, docs) | Claude | DONE | 2026-03-03 | Phase 1, 5 probes |
| 1.3 | Scoring engine + /score + /compare + /alerts | Claude | DONE | 2026-03-03 | Phase 2 |
| 1.4 | Custom domain api.oathscore.dev | Claude | DONE | 2026-03-03 | Railway CNAME |
| 1.5 | Integration tests (17/17 passing) | Claude | DONE | 2026-03-03 | tests/test_api.py |
| 1.6 | Supabase persistent storage | Claude | DONE | 2026-03-04 | Dual-write local+Supabase |
| 1.7 | All 6 API provider keys registered | Claude | DONE | 2026-03-04 | Railway env vars |
| 1.8 | MCP server (8 tools) | Claude | DONE | 2026-03-03 | oathscore_mcp package |

## Initiative 2: Billing & Monetization (COMPLETE)

| ID | Task | Owner | Status | Date | Notes |
|----|------|-------|--------|------|-------|
| 2.1 | Tighten free tier rate limits | Claude | DONE | 2026-03-04 | 10/day now, 5/day score |
| 2.2 | Stripe billing + API key system | Claude | DONE | 2026-03-04 | Live mode, real money |
| 2.3 | x402 micropayment support | Claude | DONE | 2026-03-04 | Code deployed, not activated |
| 2.4 | Founding member pricing + signup flow | Claude | DONE | 2026-03-04 | $9/mo, first 50 |
| 2.5 | Activate x402 (wallet + enable flag) | Owner | TODO | -- | Needs X402_WALLET_ADDRESS + X402_ENABLED in Railway |

## Initiative 3: Launch & Marketing (IN PROGRESS)

| ID | Task | Owner | Status | Date | Notes |
|----|------|-------|--------|------|-------|
| 3.1 | Show HN submitted | Claude | DONE | 2026-03-04 | Link post to GitHub |
| 3.2 | DEV.to article published | Claude | DONE | 2026-03-04 | "Building the Trust Layer for AI Trading Agents" |
| 3.3 | MCP directory submissions (4 dirs) | Claude | DONE | 2026-03-04 | Glama approved, 3 pending |
| 3.4 | Example agents (4: trading, monitor, crewai, langchain) | Claude | DONE | 2026-03-04 | examples/ |
| 3.5 | GitHub topics + README star CTA | Claude | DONE | 2026-03-04 | |
| 3.6 | Sample API audit report template | Claude | DONE | 2026-03-04 | docs/sample_audit_report.md |
| 3.7 | Wait for MCP directory approvals | -- | WAITING | -- | mcp.so #668, punkpeye PR #2694, mcpservers.org |
| 3.8 | Build Reddit karma (r/algotrading needs 50) | Owner | TODO | -- | Ongoing |
| 3.9 | Sponsored comparisons (approach APIs) | Claude | TODO | -- | Month 1 |
| 3.10 | Monthly "State of Financial Data APIs" report #1 | Claude | DONE | 2026-03-04 | docs/reports/2026-03-state-of-financial-data-apis.md + DEV.to version |
| 3.11 | Answer SO / GitHub discussions about MCP finance | Both | TODO | -- | Ongoing |

## Initiative 4: Code Quality & Bug Fixes (COMPLETE)

| ID | Task | Owner | Status | Date | Notes |
|----|------|-------|--------|------|-------|
| 4.1 | Fix env var name mismatch (monitor/config.py) | Claude | DONE | 2026-03-04 | CRITICAL: probes were unauthenticated |
| 4.2 | Fix example agents is_open bug | Claude | DONE | 2026-03-04 | status=="open" not is_open |
| 4.3 | Fix stale llms.txt + llms-full.txt | Claude | DONE | 2026-03-04 | Tool count, pricing, URLs |
| 4.4 | Fix MCP server default URL | Claude | DONE | 2026-03-04 | api.oathscore.dev |
| 4.5 | Fix test + CI URLs | Claude | DONE | 2026-03-04 | Was old Railway URL |
| 4.6 | Implement freshness scoring | Claude | DONE | 2026-03-04 | Bracket-based from freshness.json |
| 4.7 | Implement trust scoring | Claude | DONE | 2026-03-04 | docs+forecasts+uptime signals |
| 4.8 | Wire daily_scores to Supabase | Claude | DONE | 2026-03-04 | persist_daily_scores in scheduler |
| 4.9 | Add 2027 FOMC/CPI dates | Claude | DONE | 2026-03-04 | FIXED_EVENTS now covers 2026+2027 |
| 4.10 | Create CLAUDE.md | Claude | DONE | 2026-03-04 | Project rules for Claude Code |

## Initiative 5: AI Agent Safety (NEW)

Modeled after Curistat's production safety system. Phased by urgency.

### Phase A: Pre-Customer (NOW)

| ID | Task | Owner | Status | Priority | Notes |
|----|------|-------|--------|----------|-------|
| 5.1 | Upgrade robots.txt — block training crawlers, allow discovery bots | Claude | DONE | HIGH | 13 training crawlers blocked, 7 discovery bots allowed |
| 5.2 | Add security.txt (/.well-known/security.txt) | Claude | DONE | HIGH | RFC 9116, route added to main.py |
| 5.3 | Add kill switch (emergency API shutdown) | Claude | DONE | HIGH | Middleware checks data/kill_switch.json, 503 all routes except /health |
| 5.4 | Bot detection middleware (UA pattern matching) | Claude | TODO | MEDIUM | Block scrapers, allow known bots |
| 5.5 | Webhook rate limiting (per-IP burst + daily budget) | Claude | TODO | MEDIUM | Stripe webhook protection |

### Phase B: With Paying Customers

| ID | Task | Owner | Status | Priority | Notes |
|----|------|-------|--------|----------|-------|
| 5.6 | Agent reputation scoring (0-100, auto-throttle) | Claude | TODO | HIGH | Port from Curistat agent_reputation.py |
| 5.7 | Progressive backoff (doubling retry-after on 429s) | Claude | TODO | HIGH | Prevents hammering |
| 5.8 | Scraping/abuse pattern detection | Claude | TODO | MEDIUM | Bulk export, rapid sequential |
| 5.9 | Account enforcement escalation (warn -> suspend -> ban) | Claude | TODO | MEDIUM | Port from Curistat account_enforcement.py |
| 5.10 | Concurrency limits per API key | Claude | TODO | LOW | 2-10 concurrent by tier |

### Phase C: When Scores Are Valuable (30+ days)

| ID | Task | Owner | Status | Priority | Notes |
|----|------|-------|--------|----------|-------|
| 5.11 | Response signing (HMAC-SHA256 per agent key) | Claude | TODO | MEDIUM | Integrity verification |
| 5.12 | Data fingerprinting (daily rotating, detect redistribution) | Claude | TODO | MEDIUM | Anti-piracy |
| 5.13 | IP blocklist (permanent + timed) | Claude | TODO | LOW | Port from Curistat |
| 5.14 | Agent admin dashboard (traffic, keys, violations) | Claude | TODO | LOW | Needs website |
| 5.15 | Endpoint cooldowns (cached responses within window) | Claude | TODO | LOW | Reduce compute |

## Initiative 6: Infrastructure & Ops

| ID | Task | Owner | Status | Priority | Notes |
|----|------|-------|--------|----------|-------|
| 6.1 | Deploy latest fixes (bugs + freshness + trust + daily scores) | Claude | TODO | HIGH | `railway up` |
| 6.2 | First 30-day scores publish | -- | WAITING | -- | ~2026-04-03 |
| 6.3 | Add monitoring alerts (Telegram on probe failures) | Claude | TODO | MEDIUM | Like Curistat alert_sender |
| 6.4 | Backup strategy for monitoring data | Claude | TODO | LOW | Supabase is persistent, but no backup |
| 6.5 | Add structured logging (JSON format for Railway) | Claude | TODO | LOW | Better debugging |

---

## Status Summary

| Initiative | Total | Done | In Progress | TODO | Waiting |
|------------|-------|------|-------------|------|---------|
| 1. Core Product | 8 | 8 | 0 | 0 | 0 |
| 2. Billing | 5 | 4 | 0 | 1 | 0 |
| 3. Launch | 11 | 6 | 0 | 3 | 2 |
| 4. Bug Fixes | 10 | 10 | 0 | 0 | 0 |
| 5. AI Safety | 15 | 3 | 0 | 12 | 0 |
| 6. Infrastructure | 5 | 0 | 0 | 3 | 2 |
| **TOTAL** | **54** | **31** | **0** | **19** | **4** |

---

## Priority Queue (What To Do Next)

1. ~~5.1-5.3~~ — Pre-customer AI safety (robots.txt, security.txt, kill switch) — DONE
2. **6.1** — Deploy all pending fixes — NOW
3. **5.4-5.5** — Bot detection + webhook rate limiting — THIS WEEK
4. **3.9** — Sponsored comparisons — MONTH 1
5. **3.10** — Monthly report — MONTH 1
6. **5.6-5.9** — Agent reputation + enforcement — WHEN PAYING CUSTOMERS
7. **5.11-5.15** — Data protection — WHEN SCORES PUBLISH
