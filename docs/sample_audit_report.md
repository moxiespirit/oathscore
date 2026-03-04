# OathScore API Quality Audit Report

**Subject**: Curistat Volatility Forecast API
**Audit Period**: March 4-10, 2026 (7 days)
**Report Generated**: March 11, 2026
**Auditor**: OathScore Independent Monitoring System

---

## Executive Summary

OathScore conducted a 7-day independent audit of the Curistat API, monitoring uptime, latency, data freshness, schema stability, documentation quality, and forecast accuracy. This report presents findings across 7 quality dimensions with a composite score.

| Metric | Score | Grade |
|--------|-------|-------|
| **Composite OathScore** | **--/100** | **--** |
| Accuracy | --/100 | Pending (requires 30d) |
| Uptime | --/100 | -- |
| Freshness | --/100 | -- |
| Latency | --/100 | -- |
| Schema Stability | 100/100 | A+ |
| Documentation | --/100 | -- |
| Trust Signals | --/100 | -- |

---

## 1. Uptime & Availability

**Methodology**: Synthetic GET requests to primary endpoints every 60 seconds, 24/7.

| Endpoint | Total Pings | Successful | Failed | Uptime % |
|----------|------------|------------|--------|----------|
| /forecast/today | -- | -- | -- | --% |
| /regime | -- | -- | -- | --% |
| /signals | -- | -- | -- | --% |
| **Overall** | -- | -- | -- | **--%** |

**Observations**:
- [Downtime windows, if any]
- [Patterns: scheduled maintenance, random failures]
- [HTTP error codes observed]

**Score**: --/100

---

## 2. Latency Performance

**Methodology**: Round-trip time measured from OathScore monitoring infrastructure (Railway, US-East).

| Metric | Value |
|--------|-------|
| P50 (median) | -- ms |
| P95 | -- ms |
| P99 | -- ms |
| Max observed | -- ms |
| Avg | -- ms |

**Latency Distribution**:
- < 200ms: --% of requests
- 200-500ms: --% of requests
- 500ms-1s: --% of requests
- > 1s: --% of requests

**Score**: --/100 (normalized: <100ms = 100, >2000ms = 0)

---

## 3. Data Freshness

**Methodology**: Compare claimed data timestamps against actual measurement time, every 5 minutes.

| Check | Claimed Freshness | Actual Age | Within SLA? |
|-------|-------------------|------------|-------------|
| Forecast data | Real-time | -- seconds avg | -- |
| Regime indicator | 5-min refresh | -- seconds avg | -- |

**Score**: --/100

---

## 4. Schema Stability

**Methodology**: Hash response JSON structure hourly. Flag any structural changes.

| Period | Schema Changes | Breaking Changes |
|--------|---------------|-----------------|
| Week 1 | 0 | 0 |

**Details**: No schema changes detected during the audit period. Response structure remained consistent across all endpoints.

**Score**: 100/100

---

## 5. Forecast Accuracy (Preview)

**Methodology**: Snapshot daily forecasts, compare to actual outcomes next trading day using Yahoo Finance as ground truth.

*Note: Full accuracy scoring requires 30 days of data. This section provides preliminary observations.*

| Date | Forecast Range | Actual Range | Direction Correct? |
|------|---------------|-------------|-------------------|
| -- | -- | -- | -- |

**Preliminary Assessment**: [Observations from available data]

**Score**: Pending (30-day minimum)

---

## 6. Documentation Quality

**Methodology**: Check for industry-standard documentation artifacts.

| Artifact | Present? | Quality |
|----------|----------|---------|
| OpenAPI/Swagger spec | -- | -- |
| llms.txt (agent-readable) | -- | -- |
| API reference docs | -- | -- |
| Authentication docs | -- | -- |
| Rate limit documentation | -- | -- |
| Example requests/responses | -- | -- |
| Changelog/versioning | -- | -- |
| Status page | -- | -- |

**Score**: --/100

---

## 7. Trust Signals

**Methodology**: Check for transparency and reliability indicators.

| Signal | Present? |
|--------|----------|
| Published accuracy metrics | -- |
| Signed/authenticated responses | -- |
| ETag/caching support | -- |
| CORS headers | -- |
| Rate limit headers | -- |
| Semantic versioning | -- |

**Score**: --/100

---

## Comparison Context

How does this API compare to peers in the financial data space?

| API | Composite Score | Best At | Weakest At |
|-----|----------------|---------|------------|
| Subject API | -- | -- | -- |
| Peer Average (6 APIs) | -- | -- | -- |
| Best in Class | -- | -- | -- |

---

## Recommendations

Based on our audit findings, we recommend the following improvements:

1. **[Priority 1]**: [Specific recommendation]
2. **[Priority 2]**: [Specific recommendation]
3. **[Priority 3]**: [Specific recommendation]

---

## Methodology Notes

- All monitoring is conducted from OathScore infrastructure, independent of the API provider
- Scores are calculated using OathScore's published methodology: https://api.oathscore.dev/docs
- Accuracy component weighted 35% — highest weight because data correctness is what agents pay for
- Full methodology: https://github.com/moxiespirit/oathscore/blob/main/docs/METHODOLOGY.md

---

## About OathScore

OathScore is the independent quality rating system for financial data APIs. We continuously monitor accuracy, uptime, freshness, latency, and reliability of data APIs used by AI trading agents.

**Contact**: [email]
**API**: https://api.oathscore.dev
**GitHub**: https://github.com/moxiespirit/oathscore

---

*This report was generated by OathScore's automated monitoring system. OathScore has no financial relationship with the audited API provider. All data is collected independently.*
