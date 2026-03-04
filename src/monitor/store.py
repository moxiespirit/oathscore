"""Storage layer for monitoring data. Starts with local JSON files, swap to Supabase later."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "monitor"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Keep last N entries per file to avoid unbounded growth
MAX_ENTRIES = 10000


def _load(filename: str) -> list:
    path = DATA_DIR / filename
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return []
    return []


def _save(filename: str, data: list):
    path = DATA_DIR / filename
    # Trim to max entries
    if len(data) > MAX_ENTRIES:
        data = data[-MAX_ENTRIES:]
    path.write_text(json.dumps(data, indent=None))


async def store_ping(result: dict):
    data = _load("pings.json")
    data.append(result)
    _save("pings.json", data)


async def store_schema(result: dict):
    data = _load("schemas.json")
    data.append(result)
    _save("schemas.json", data)


async def get_last_schema_hash(api_name: str, endpoint: str) -> str | None:
    data = _load("schemas.json")
    for entry in reversed(data):
        if entry.get("api_name") == api_name and entry.get("endpoint") == endpoint:
            return entry.get("schema_hash")
    return None


async def store_docs_check(result: dict):
    data = _load("docs_checks.json")
    data.append(result)
    _save("docs_checks.json", data)


async def store_freshness(result: dict):
    data = _load("freshness.json")
    data.append(result)
    _save("freshness.json", data)


async def get_latest_scores() -> dict:
    """Get the most recent monitoring data for each API, for the /score endpoint."""
    pings = _load("pings.json")
    schemas = _load("schemas.json")
    docs = _load("docs_checks.json")

    scores = {}
    # Build per-API summaries from recent data
    for api_name in set(p.get("api_name") for p in pings[-500:]):
        api_pings = [p for p in pings[-500:] if p.get("api_name") == api_name]
        if not api_pings:
            continue

        ok_count = sum(1 for p in api_pings if p.get("ok"))
        total = len(api_pings)
        avg_latency = sum(p.get("latency_ms", 0) for p in api_pings if p.get("ok")) / max(ok_count, 1)

        # Schema stability
        api_schemas = [s for s in schemas if s.get("api_name") == api_name]
        schema_changes = sum(1 for s in api_schemas[-30:] if s.get("changed"))

        # Docs score
        api_docs = [d for d in docs if d.get("api_name") == api_name]
        docs_score = api_docs[-1].get("score", 0) if api_docs else 0

        scores[api_name] = {
            "uptime_pct": round(ok_count / total * 100, 1) if total > 0 else None,
            "avg_latency_ms": round(avg_latency),
            "total_pings": total,
            "schema_changes_30d": schema_changes,
            "docs_score": docs_score,
            "last_ping": api_pings[-1].get("timestamp"),
        }

    return scores
