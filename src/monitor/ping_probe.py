"""Uptime and latency monitoring probe."""

import logging
import time
from datetime import datetime, timezone

import httpx

from src.monitor.config import MONITORED_APIS, get_api_key, get_api_secret
from src.monitor.store import store_ping

logger = logging.getLogger(__name__)


async def ping_all() -> list[dict]:
    """Ping all monitored APIs and record results."""
    results = []
    async with httpx.AsyncClient(timeout=15.0) as client:
        for api_name, api in MONITORED_APIS.items():
            # Ping health endpoint or first sample endpoint
            endpoints = []
            if api.get("health"):
                endpoints.append({"path": api["health"], "params": {}})
            for ep in api.get("endpoints", []):
                params = dict(ep.get("params", {}))
                headers = dict(ep.get("headers", {}))
                key = get_api_key(api_name)
                secret = get_api_secret(api_name)
                # Substitute {key} and {secret} in params and headers
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
                endpoints.append({"path": ep["path"], "params": params, "headers": headers})

            for ep in endpoints:
                url = f"{api['base_url']}{ep['path']}"
                result = {
                    "api_name": api_name,
                    "endpoint": ep["path"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                try:
                    start = time.monotonic()
                    resp = await client.get(url, params=ep.get("params", {}), headers=ep.get("headers", {}))
                    latency_ms = int((time.monotonic() - start) * 1000)
                    result["status_code"] = resp.status_code
                    result["latency_ms"] = latency_ms
                    result["ok"] = 200 <= resp.status_code < 400
                except httpx.TimeoutException:
                    result["status_code"] = 0
                    result["latency_ms"] = 15000
                    result["ok"] = False
                    result["error"] = "timeout"
                except Exception as e:
                    result["status_code"] = 0
                    result["latency_ms"] = 0
                    result["ok"] = False
                    result["error"] = str(e)[:200]

                results.append(result)
                await store_ping(result)
                logger.info("Ping %s%s: %s %dms", api_name, ep["path"], result.get("status_code"), result.get("latency_ms", 0))

    return results
