# OathScore Methodology

> Every API makes promises. OathScore checks the receipts.

This document describes exactly how OathScore computes its ratings. We publish this because **transparency is the product**. If you can't see how the score is computed, you can't trust it.

---

## Composite Score (0-100)

Every rated API receives a composite score from 0 to 100, updated daily.

| Component | Weight | What It Measures |
|-----------|--------|-----------------|
| **Accuracy** | 35% | Does the API return correct data? |
| **Uptime** | 20% | Is the API available when you need it? |
| **Freshness** | 15% | Is the data as current as claimed? |
| **Latency** | 15% | How fast does the API respond? |
| **Schema Stability** | 5% | Does the API break its contract? |
| **Documentation** | 5% | Can an agent self-integrate? |
| **Trust Signals** | 5% | Does the API welcome scrutiny? |

### Letter Grades

| Grade | Score Range | Meaning |
|-------|-----------|---------|
| A+ | 95-100 | Exceptional across all dimensions |
| A | 90-94 | Excellent, minor gaps |
| B | 80-89 | Good, some areas need improvement |
| C | 70-79 | Acceptable, notable weaknesses |
| D | 60-69 | Below average, multiple concerns |
| F | 0-59 | Unreliable, agents should avoid |

---

## Component Details

### Accuracy (35%)

The most important component. Agents buy data to make decisions. Wrong data = wrong decisions = lost money.

**For forecast/prediction APIs:**
- Record the forecast at time of publication
- Compare to actual outcome the next trading day
- Track: Mean Absolute Error (MAE), directional accuracy (%), calibration
- Rolling 30-day and 90-day windows
- Score = 100 * (1 - normalized_error), capped at 0

**For data-only APIs (quotes, historical, fundamentals):**
- Compare returned values against a reference source (e.g., CBOE official close for VIX)
- Track: deviation from reference, missing data points, completeness
- Score = 100 * (correct_responses / total_checks)

**For calendar/event APIs:**
- Did the event happen when claimed?
- Was the consensus value correct?
- Were surprise events caught in advance?
- Score = 100 * (correct_events / total_events)

### Uptime (20%)

- Synthetic monitoring: ping each endpoint every 60 seconds, 24/7
- A "successful" ping: HTTP 2xx response with valid JSON body
- Score = 100 * (successful_pings / total_pings) over rolling 30 days
- Example: 99.5% uptime = score of 99.5

### Freshness (15%)

- Check the age of data returned by each endpoint
- Compare actual data age against the API's claimed update frequency
- Example: API claims "real-time" but data is 15 minutes old = penalty
- Score = 100 * (checks_within_claimed_freshness / total_checks)

### Latency (15%)

- Measure response time (P50, P95, P99) from our monitoring location
- Normalize against category average:
  - Quote APIs: P50 < 100ms = score 100, > 2000ms = score 0
  - Forecast APIs: P50 < 500ms = score 100, > 5000ms = score 0
- Linear interpolation between thresholds
- Measured from US East (Railway, closest to most financial APIs)

### Schema Stability (5%)

- Hash the response schema (field names, types, nesting) daily
- Each breaking change in 30 days: -20 points
- 0 breaking changes = score 100
- 5+ breaking changes = score 0
- Non-breaking additions (new optional fields) are not penalized

### Documentation (5%)

Checklist scoring:

| Item | Points |
|------|--------|
| OpenAPI 3.0+ spec published | 25 |
| llms.txt at domain root | 25 |
| Code examples in docs | 20 |
| Error response documentation | 15 |
| Rate limit documentation | 15 |

### Trust Signals (5%)

Checklist scoring:

| Item | Points |
|------|--------|
| Publishes accuracy/quality metrics | 30 |
| Response signing (HMAC, JWT, etc.) | 25 |
| ETag / conditional request support | 15 |
| Public status page | 15 |
| Data provenance headers (X-Data-Age, etc.) | 15 |

---

## Monitoring Infrastructure

- **Ping frequency**: Every 60 seconds for uptime/latency
- **Freshness checks**: Every 5 minutes
- **Forecast snapshots**: Hourly during market hours
- **Accuracy verification**: Daily (compare yesterday's forecasts to actuals)
- **Schema checks**: Daily
- **Documentation checks**: Weekly

All monitoring runs from a single location (US East). We do not claim to measure global latency. Regional latency may vary.

## Data Retention

- Raw ping data: 90 days
- Daily scores: indefinite (this IS the moat)
- Forecast snapshots: indefinite
- Schema snapshots: 1 year

## Conflicts of Interest

OathScore is operated independently. We rate APIs that may compete with services operated by our team members. To maintain credibility:

1. **Same methodology for everyone**: No API gets special treatment, including our own.
2. **Public methodology**: This document is the complete scoring methodology. Nothing hidden.
3. **Raw data available**: Paid tiers can access raw monitoring data to verify our scores independently.
4. **Disputes**: Any rated API can dispute their score. We will publish the dispute and our response.

---

## Changelog

| Date | Change |
|------|--------|
| 2026-03-03 | Initial methodology published |

---

*Questions about our methodology? Open an issue on our GitHub repository.*
