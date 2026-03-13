# OathScore Document Index

**Last Updated**: 2026-03-12

## Root

| Document | Audience | Description |
|----------|----------|-------------|
| [README.md](../README.md) | Public | Product overview, pricing, quick start, examples |
| [CLAUDE.md](../CLAUDE.md) | AI Assistant | Project instructions, architecture summary, rules |
| [CHANGELOG.md](../CHANGELOG.md) | All | Change history by date |

## docs/

| Document | Audience | Description |
|----------|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Developer | System diagram, component map, data flow, infrastructure |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Operator | Deploy commands, env vars, DNS, rollback |
| [REFERENCE_MANUAL.md](REFERENCE_MANUAL.md) | Operator | Complete operational reference (22 sections) |
| [METHODOLOGY.md](METHODOLOGY.md) | Public | Scoring methodology: 7 components, weights, grading |
| [BUSINESS_CONCEPT.md](BUSINESS_CONCEPT.md) | Internal | Business model, flywheel, competitive analysis |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Developer | Original build plan and phase breakdown |
| [START_HERE.md](START_HERE.md) | AI Assistant | Session startup fallback guide |
| [ALERT_REGISTRY.md](ALERT_REGISTRY.md) | Operator | Alert types, thresholds, escalation rules |
| [HEALTHCHECK_SCHEDULE.md](HEALTHCHECK_SCHEDULE.md) | Operator | Probe intervals and health check schedule |
| [ISSUE_ESCALATION_PLAYBOOK.md](ISSUE_ESCALATION_PLAYBOOK.md) | Operator | Incident response procedures |
| [MCP_REGISTRATION.md](MCP_REGISTRATION.md) | Developer | MCP directory registration status |
| [launch_posts.md](launch_posts.md) | Marketing | Reddit/HN/Twitter launch post drafts |
| [sample_audit_report.md](sample_audit_report.md) | Sales | Template for $299-499 API audit reports |
| [INDEX.md](INDEX.md) | All | This file |

## docs/reports/

| Document | Audience | Description |
|----------|----------|-------------|
| [2026-03-state-of-financial-data-apis.md](reports/2026-03-state-of-financial-data-apis.md) | Public | State of Financial Data APIs report |

## tracking/

| Document | Audience | Description |
|----------|----------|-------------|
| [OATHSCORE_SESSION.md](../tracking/OATHSCORE_SESSION.md) | AI Assistant | Current session state (read first every session) |
| [OATHSCORE_SESSION_UPDATE_20260308.md](../tracking/OATHSCORE_SESSION_UPDATE_20260308.md) | AI Assistant | Session update snapshot |
| [PROJECT_TRACKER.md](../tracking/PROJECT_TRACKER.md) | Operator | Task status and project milestones |
| [OWNER_NOTES.md](../tracking/OWNER_NOTES.md) | AI Assistant | Standing owner instructions |

## .claude/skills/

| Document | Audience | Description |
|----------|----------|-------------|
| [oathscore-guardian/skill.md](../.claude/skills/oathscore-guardian/skill.md) | AI Assistant | Session startup audit skill |
| [oathscore-audit/skill.md](../.claude/skills/oathscore-audit/skill.md) | AI Assistant | Forensic verification skill |
| [oathscore-session/skill.md](../.claude/skills/oathscore-session/skill.md) | AI Assistant | Session management skill |

## public/

| File | Description |
|------|-------------|
| `robots.txt` | Bot access policy (20 blocked crawlers, 7 discovery bots allowed) |
| `llms.txt` | Agent-readable product summary |
| `llms-full.txt` | Complete agent documentation |
| `ai.txt` | AI discovery pointer |
| `terms.txt` | Terms of Service (API usage, training prohibition) |
