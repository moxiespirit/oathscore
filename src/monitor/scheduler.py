"""Monitoring scheduler — runs probes on intervals."""

import asyncio
import logging

from src.monitor.ping_probe import ping_all
from src.monitor.schema_probe import check_schemas
from src.monitor.docs_probe import check_docs
from src.monitor.freshness_probe import check_freshness

logger = logging.getLogger(__name__)

PING_INTERVAL = 60        # Every 60 seconds
FRESHNESS_INTERVAL = 300  # Every 5 minutes
SCHEMA_INTERVAL = 3600    # Every hour
DOCS_INTERVAL = 86400     # Every 24 hours


async def _run_loop(name: str, func, interval: int):
    """Run a probe function on a fixed interval."""
    while True:
        try:
            logger.info("Running %s probe", name)
            await func()
        except Exception as e:
            logger.error("Probe %s failed: %s", name, e)
        await asyncio.sleep(interval)


async def start_monitoring():
    """Start all monitoring loops as background tasks."""
    tasks = [
        asyncio.create_task(_run_loop("ping", ping_all, PING_INTERVAL)),
        asyncio.create_task(_run_loop("freshness", check_freshness, FRESHNESS_INTERVAL)),
        asyncio.create_task(_run_loop("schema", check_schemas, SCHEMA_INTERVAL)),
        asyncio.create_task(_run_loop("docs", check_docs, DOCS_INTERVAL)),
    ]
    return tasks
