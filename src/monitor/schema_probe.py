"""Schema change detection probe."""

import hashlib
import json
import logging
from datetime import datetime, timezone

import httpx

from src.monitor.config import MONITORED_APIS, get_api_key, get_api_secret
from src.monitor.store import store_schema, get_last_schema_hash

logger = logging.getLogger(__name__)


def _extract_schema(data) -> dict:
    """Extract structure (keys and types) from a JSON response."""
    if isinstance(data, dict):
        return {k: _extract_schema(v) for k, v in sorted(data.items())}
    elif isinstance(data, list):
        if data:
            return [_extract_schema(data[0])]
        return ["empty"]
    else:
        return type(data).__name__


def _hash_schema(schema: dict) -> str:
    """SHA-256 hash of the schema structure."""
    return hashlib.sha256(json.dumps(schema, sort_keys=True).encode()).hexdigest()[:16]


async def check_schemas() -> list[dict]:
    """Check all API response schemas for changes."""
    results = []
    async with httpx.AsyncClient(timeout=15.0) as client:
        for api_name, api in MONITORED_APIS.items():
            for ep in api.get("endpoints", []):
                params = dict(ep.get("params", {}))
                headers = dict(ep.get("headers", {}))
                key = get_api_key(api_name)
                secret = get_api_secret(api_name)
                if key:
                    params = {k: (key if v == "{key}" else v) for k, v in params.items()}
                    headers = {k: (key if v == "{key}" else v) for k, v in headers.items()}
                elif any(v == "{key}" for v in params.values()) or any(v == "{key}" for v in headers.values()):
                    continue
                if secret:
                    params = {k: (secret if v == "{secret}" else v) for k, v in params.items()}
                    headers = {k: (secret if v == "{secret}" else v) for k, v in headers.items()}
                elif any(v == "{secret}" for v in params.values()) or any(v == "{secret}" for v in headers.values()):
                    continue

                url = f"{api['base_url']}{ep['path']}"
                try:
                    resp = await client.get(url, params=params, headers=headers)
                    if resp.status_code != 200:
                        continue
                    data = resp.json()
                    schema = _extract_schema(data)
                    schema_hash = _hash_schema(schema)
                    prev_hash = await get_last_schema_hash(api_name, ep["path"])
                    changed = prev_hash is not None and prev_hash != schema_hash

                    result = {
                        "api_name": api_name,
                        "endpoint": ep["path"],
                        "schema_hash": schema_hash,
                        "changed": changed,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    if changed:
                        result["schema"] = schema
                        logger.warning("Schema change detected: %s %s (%s -> %s)", api_name, ep["path"], prev_hash, schema_hash)

                    await store_schema(result)
                    results.append(result)
                except Exception as e:
                    logger.warning("Schema check failed for %s %s: %s", api_name, ep["path"], e)

    return results
