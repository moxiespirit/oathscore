"""Composite scoring engine — computes OathScore ratings from raw monitoring data."""

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

    # Accuracy: placeholder until forecast verification is built
    accuracy_score = None
    has_accuracy = MONITORED_APIS.get(api_name, {}).get("has_forecasts", False)

    # Freshness: placeholder
    freshness_score = None

    # Trust signals: placeholder
    trust_score = 50  # Default mid-range

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
