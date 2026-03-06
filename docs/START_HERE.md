# OathScore — Start Here

Quick reference for new or crashed sessions. Read in this order:

## 1. Run the guardian
```
/oathscore-guardian
```
This automates everything below. If the skill is unavailable, read manually:

## 2. Manual fallback (read in order)
1. `CLAUDE.md` — project rules
2. `tracking/OATHSCORE_SESSION.md` — full state (architecture, endpoints, credentials, file map, decisions)
3. `tracking/PROJECT_TRACKER.md` — task list with priorities
4. `tracking/OWNER_NOTES.md` — owner instructions + GitHub issue sync

## 3. Operational docs (read when relevant)
- `docs/HEALTHCHECK_SCHEDULE.md` — what runs, when, failure handling
- `docs/ALERT_REGISTRY.md` — all 9 alert types, Telegram config, dedup
- `docs/ISSUE_ESCALATION_PLAYBOOK.md` — known failures + predetermined fixes

## 4. Key facts
- **API**: https://api.oathscore.dev
- **Repo**: https://github.com/moxiespirit/oathscore
- **Hosting**: Railway ($5/mo), Docker, FastAPI
- **Storage**: Dual-write (local JSON + Supabase)
- **Billing**: Stripe (live), x402 (dormant)
- **Alerts**: Telegram only (TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID)
- **Deploy**: `railway up` from repo root
