"""Supabase storage backend — persistent storage for monitoring data.

Falls back to local JSON if Supabase is not configured.
"""

import json
import logging
import os
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")

_client: httpx.Client | None = None


def _get_client() -> httpx.Client | None:
    global _client
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    if _client is None:
        _client = httpx.Client(
            base_url=f"{SUPABASE_URL}/rest/v1",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            timeout=10.0,
        )
    return _client


def is_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


async def insert(table: str, data: dict) -> bool:
    """Insert a row into a Supabase table."""
    client = _get_client()
    if not client:
        return False
    try:
        resp = client.post(f"/{table}", json=data)
        if resp.status_code in (200, 201):
            return True
        logger.warning("Supabase insert %s failed: %s %s", table, resp.status_code, resp.text[:200])
        return False
    except Exception as e:
        logger.warning("Supabase insert %s error: %s", table, e)
        return False


async def query(table: str, params: dict | None = None, limit: int = 100) -> list[dict]:
    """Query rows from a Supabase table."""
    client = _get_client()
    if not client:
        return []
    try:
        query_params = params or {}
        query_params["limit"] = str(limit)
        query_params["order"] = "id.desc"
        resp = client.get(f"/{table}", params=query_params)
        if resp.status_code == 200:
            return resp.json()
        logger.warning("Supabase query %s failed: %s", table, resp.status_code)
        return []
    except Exception as e:
        logger.warning("Supabase query %s error: %s", table, e)
        return []


async def query_last(table: str, filters: dict) -> dict | None:
    """Get the most recent row matching filters."""
    client = _get_client()
    if not client:
        return None
    try:
        params = {"limit": "1", "order": "id.desc"}
        for k, v in filters.items():
            params[k] = f"eq.{v}"
        resp = client.get(f"/{table}", params=params)
        if resp.status_code == 200:
            rows = resp.json()
            return rows[0] if rows else None
        return None
    except Exception:
        return None
