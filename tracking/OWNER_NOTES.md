# OathScore Owner Notes

**Last Updated**: 2026-03-05

Shared notification system between Owner and Claude. Synced from GitHub issues.

---

## Notification Protocol

- **Owner -> Claude**: Create GitHub issue with `waiting-claude` label, or write notes below
- **Claude -> Owner**: Create GitHub issue with `waiting-owner` label
- **Sync**: At session start, run `gh issue list --label waiting-claude` and `gh issue list --label waiting-owner`

---

## Open Items From Owner (waiting-claude)

_Sync from: `gh issue list --label waiting-claude --repo moxiespirit/oathscore`_

(none currently)

---

## Open Items For Owner (waiting-owner)

_Sync from: `gh issue list --label waiting-owner --repo moxiespirit/oathscore`_

(none currently)

---

## Owner Notes (Free-Form)

### 2026-03-05
- Set up Telegram bot credentials in Railway (TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID)
- SendGrid rejected (has a cost) — Telegram only for alerts
- Wants Curistat-style documentation system for cross-session continuity

---

## Recurring Checks

- [ ] Check MCP directory approvals (mcp.so #668, punkpeye PR #2694, mcpservers.org)
- [ ] Check HN post performance
- [ ] Check DEV.to article stats
- [ ] Check Stripe dashboard for subscribers
- [ ] Verify API health: `curl https://api.oathscore.dev/health`
