"""Composite scoring engine — computes OathScore ratings from raw monitoring data."""

import json
import logging
from src.monitor.store import _load
from src.monitor.config import MONITORED_APIS

logger = logging.getLogger(__name__)

# Weights from METHODOLOGY.md
WEIGHTS = {
    "accuracy": 0.35,
    "uptime": 0.20,
    "freshness": 0.15,
    "latency": 0.15,
    "schema": 0.05,
    "docs": 0.05,
    "trust": 0.05,
}

# Latency thresholds (ms) -> score
# <200ms = 100, <500ms = 80, <1000ms = 60, <2000ms = 40, <5000ms = 20, >5000ms = 0
LATENCY_BRACKETS = [
    (200, 100), (500, 80), (1000, 60), (2000, 40), (5000, 20),
]


def _latency_score(avg_ms: float) -> float:
    for threshold, score in LATENCY_BRACKETS:
        if avg_ms < threshold:
            return score
    return 0


def _letter_grade(score: float) -> str:
    if score >= 97:
        return "A+"
    elif score >= 93:
        return "A"
    elif score >= 90:
        return "A-"
    elif score >= 87:
        return "B+"
    elif score >= 83:
        return "B"
    elif score >= 80:
        return "B-"
    elif score >= 77:
        return "C+"
    elif score >= 73:
        return "C"
    elif score >= 70:
        return "C-"
    elif score >= 60:
        return "D"
    else:
        return "F"


def compute_score(api_name: str) -> dict | None:
    """Compute composite OathScore for an API from stored monitoring data."""
    pings = _load("pings.json")
    schemas = _load("schemas.json")
    docs = _load("docs_checks.json")

    api_pings = [p for p in pings if p.get("api_name") == api_name]
    if len(api_pings) < 10:
        return None  # Not enough data

    # Uptime: % of successful pings
    ok_count = sum(1 for p in api_pings if p.get("ok"))
    uptime = ok_count / len(api_pings) * 100

    # Latency: avg of successful pings
    ok_latencies = [p.get("latency_ms", 0) for p in api_pings if p.get("ok")]
    avg_latency = sum(ok_latencies) / len(ok_latencies) if ok_latencies else 5000

    # Schema stability: % of checks with no changes
    api_schemas = [s for s in schemas if s.get("api_name") == api_name]
    if api_schemas:
        stable = sum(1 for s in api_schemas if not s.get("changed"))
        schema_score = stable / len(api_schemas) * 100
    else:
        schema_score = 100  # No checks = assume stable

    # Docs: latest score
    api_docs = [d for d in docs if d.get("api_name") == api_name]
    docs_score = api_docs[-1].get("score", 0) if api_docs else 0

    # Accuracy: from verified forecast snapshots
    accuracy_score = None
    has_accuracy = MONITORED_APIS.get(api_name, {}).get("has_forecasts", False)
    if has_accuracy:
        snapshots = _load("forecast_snapshots.json")
        verified = [s for s in snapshots if s.get("api_name") == api_name and s.get("accuracy_score") is not None]
        if len(verified) >= 5:
            accuracy_score = sum(s["accuracy_score"] for s in verified[-30:]) / len(verified[-30:])

    # Freshness: score from freshness probe data (age_seconds)
    freshness_data = _load("freshness.json")
    api_freshness = [f for f in freshness_data if f.get("api_name") == api_name and f.get("age_seconds") is not None]
    if api_freshness:
        recent = api_freshness[-10:]  # Last 10 checks
        avg_age = sum(f["age_seconds"] for f in recent) / len(recent)
        # <60s = 100, <300s = 90, <900s = 75, <3600s = 50, <86400s = 25, >86400 = 0
        if avg_age < 60:
            freshness_score = 100
        elif avg_age < 300:
            freshness_score = 90
        elif avg_age < 900:
            freshness_score = 75
        elif avg_age < 3600:
            freshness_score = 50
        elif avg_age < 86400:
            freshness_score = 25
        else:
            freshness_score = 0
    else:
        freshness_score = None

    # Trust signals: based on docs quality, published accuracy data, transparency
    api_cfg = MONITORED_APIS.get(api_name, {})
    trust_score = 30  # Base
    api_docs_list = [d for d in _load("docs_checks.json") if d.get("api_name") == api_name]
    if api_docs_list and api_docs_list[-1].get("score", 0) >= 60:
        trust_score += 25  # Good docs
    if api_cfg.get("has_forecasts"):
        trust_score += 25  # Publishes verifiable forecasts
    if uptime >= 99:
        trust_score += 20  # High reliability signals trust

    # Composite (skip components we can't measure yet)
    components = {
        "uptime": {"score": round(uptime, 1), "weight": WEIGHTS["uptime"]},
        "latency": {"score": round(_latency_score(avg_latency), 1), "weight": WEIGHTS["latency"]},
        "schema": {"score": round(schema_score, 1), "weight": WEIGHTS["schema"]},
        "docs": {"score": round(docs_score, 1), "weight": WEIGHTS["docs"]},
        "trust": {"score": trust_score, "weight": WEIGHTS["trust"]},
    }
    if accuracy_score is not None:
        components["accuracy"] = {"score": accuracy_score, "weight": WEIGHTS["accuracy"]}
    if freshness_score is not None:
        components["freshness"] = {"score": freshness_score, "weight": WEIGHTS["freshness"]}

    # Reweight to available components
    total_weight = sum(c["weight"] for c in components.values())
    composite = sum(c["score"] * c["weight"] for c in components.values()) / total_weight

    return {
        "api": api_name,
        "composite_score": round(composite, 1),
        "grade": _letter_grade(composite),
        "components": components,
        "data_points": len(api_pings),
        "monitoring_since": api_pings[0].get("timestamp") if api_pings else None,
        "note": "Accuracy and freshness scores pending (require 30+ days of data)" if accuracy_score is None else None,
    }


def compute_all_scores() -> dict:
    """Compute scores for all APIs that have enough data."""
    results = {}
    for api_name in MONITORED_APIS:
        score = compute_score(api_name)
        if score:
            results[api_name] = score
    return results


async def persist_daily_scores():
    """Compute and write all scores to Supabase daily_scores table."""
    from src.monitor import supabase_store as supa
    from datetime import datetime, timezone

    scores = compute_all_scores()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for api_name, score in scores.items():
        await supa.insert("daily_scores", {
            "api_name": api_name,
            "date": today,
            "composite_score": score["composite_score"],
            "grade": score["grade"],
            "components": json.dumps(score["components"]),
            "data_points": score["data_points"],
        })
    logger.info("Persisted daily scores for %d APIs", len(scores))
