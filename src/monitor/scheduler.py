"""Monitoring scheduler — runs probes on intervals, triggers alerts."""

import asyncio
import logging

from src.monitor.ping_probe import ping_all
from src.monitor.schema_probe import check_schemas
from src.monitor.docs_probe import check_docs
from src.monitor.freshness_probe import check_freshness
from src.monitor.accuracy_probe import snapshot_forecasts, verify_forecasts
from src.monitor.scoring import persist_daily_scores
from src.monitor.alerts import check_and_alert
from src.monitor.alert_sender import send_daily_digest

logger = logging.getLogger(__name__)

PING_INTERVAL = 60         # Every 60 seconds
FRESHNESS_INTERVAL = 300   # Every 5 minutes
SCHEMA_INTERVAL = 3600     # Every hour
SNAPSHOT_INTERVAL = 3600   # Snapshot forecasts every hour
VERIFY_INTERVAL = 86400    # Verify accuracy daily
DOCS_INTERVAL = 86400      # Every 24 hours
DAILY_SCORES_INTERVAL = 86400  # Persist scores daily
ALERT_CHECK_INTERVAL = 300    # Check alerts every 5 minutes
DIGEST_INTERVAL = 86400       # Daily digest


async def _run_loop(name: str, func, interval: int):
    """Run a probe function on a fixed interval."""
    while True:
        try:
            logger.info("Running %s probe", name)
            await func()
        except Exception as e:
            logger.error("Probe %s failed: %s", name, e)
        await asyncio.sleep(interval)


async def _run_sync_loop(name: str, func, interval: int):
    """Run a sync function on a fixed interval (for alert checks)."""
    while True:
        try:
            logger.info("Running %s", name)
            func()
        except Exception as e:
            logger.error("%s failed: %s", name, e)
        await asyncio.sleep(interval)


async def start_monitoring():
    """Start all monitoring loops as background tasks."""
    tasks = [
        asyncio.create_task(_run_loop("ping", ping_all, PING_INTERVAL)),
        asyncio.create_task(_run_loop("freshness", check_freshness, FRESHNESS_INTERVAL)),
        asyncio.create_task(_run_loop("schema", check_schemas, SCHEMA_INTERVAL)),
        asyncio.create_task(_run_loop("snapshot", snapshot_forecasts, SNAPSHOT_INTERVAL)),
        asyncio.create_task(_run_loop("verify", verify_forecasts, VERIFY_INTERVAL)),
        asyncio.create_task(_run_loop("docs", check_docs, DOCS_INTERVAL)),
        asyncio.create_task(_run_loop("daily_scores", persist_daily_scores, DAILY_SCORES_INTERVAL)),
        asyncio.create_task(_run_sync_loop("alert_check", check_and_alert, ALERT_CHECK_INTERVAL)),
        asyncio.create_task(_run_sync_loop("daily_digest", send_daily_digest, DIGEST_INTERVAL)),
    ]
    return tasks
