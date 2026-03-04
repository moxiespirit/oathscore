"""Documentation quality probe — checks for OpenAPI, llms.txt, etc."""

import logging
from datetime import datetime, timezone

import httpx

from src.monitor.config import MONITORED_APIS
from src.monitor.store import store_docs_check

logger = logging.getLogger(__name__)

# Discovery files to check
DISCOVERY_FILES = [
    "/openapi.json",
    "/llms.txt",
    "/llms-full.txt",
    "/.well-known/ai-plugin.json",
    "/robots.txt",
]


async def check_docs() -> list[dict]:
    """Check documentation quality for all monitored APIs."""
    results = []
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        for api_name, api in MONITORED_APIS.items():
            base = api["base_url"]
            docs_url = api.get("docs_url", "")
            found = []
            missing = []

            for path in DISCOVERY_FILES:
                try:
                    resp = await client.get(f"{base}{path}")
                    if resp.status_code == 200 and len(resp.content) > 10:
                        found.append(path)
                    else:
                        missing.append(path)
                except Exception:
                    missing.append(path)

            # Check if docs_url is accessible
            docs_accessible = False
            if docs_url:
                try:
                    resp = await client.get(docs_url)
                    docs_accessible = resp.status_code == 200
                except Exception:
                    pass

            score = len(found) / len(DISCOVERY_FILES) * 80  # 80% for discovery files
            if docs_accessible:
                score += 20  # 20% for having docs

            result = {
                "api_name": api_name,
                "found": found,
                "missing": missing,
                "docs_accessible": docs_accessible,
                "score": round(score, 1),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            results.append(result)
            await store_docs_check(result)
            logger.info("Docs check %s: %.0f/100 (%d/%d files)", api_name, score, len(found), len(DISCOVERY_FILES))

    return results
