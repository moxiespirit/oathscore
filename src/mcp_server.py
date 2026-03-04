"""OathScore MCP Server — tools for AI agents."""

import json
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "oathscore",
    description="Real-time world state and API quality ratings for trading agents.",
)

BASE_URL = "https://api.oathscore.dev"
_client = httpx.Client(timeout=15)


def _get(path: str, params: dict | None = None) -> dict:
    """GET request to OathScore API."""
    resp = _client.get(f"{BASE_URL}{path}", params=params)
    resp.raise_for_status()
    return resp.json()


@mcp.tool()
def get_now() -> str:
    """Get current world state: exchange status, volatility (VIX/VVIX/SKEW/term structure), economic event countdowns, and data health. One call replaces 4-6 separate API calls."""
    data = _get("/now")
    return json.dumps(data, indent=2)


@mcp.tool()
def get_exchanges() -> str:
    """Get open/close status for CME, NYSE, NASDAQ, LSE, EUREX, TSE, HKEX with next transition times."""
    data = _get("/now")
    return json.dumps(data.get("exchanges", {}), indent=2)


@mcp.tool()
def get_volatility() -> str:
    """Get current volatility readings: VIX, VIX9D, VIX3M, VVIX, SKEW, and term structure (contango/backwardation/flat)."""
    data = _get("/now")
    return json.dumps(data.get("volatility", {}), indent=2)


@mcp.tool()
def get_events() -> str:
    """Get economic event countdowns: next event, today remaining, week high-impact count, days until FOMC and CPI."""
    data = _get("/now")
    return json.dumps(data.get("events", {}), indent=2)


@mcp.tool()
def get_score(api_name: str) -> str:
    """Get OathScore quality rating for a specific API. Available APIs: curistat, alphavantage, polygon, finnhub, twelvedata, eodhd, fmp. Returns composite score (0-100), letter grade, and component breakdown."""
    data = _get(f"/score/{api_name}")
    return json.dumps(data, indent=2)


@mcp.tool()
def compare_apis(apis: str) -> str:
    """Compare quality scores of two or more APIs side-by-side. Pass comma-separated names, e.g. 'curistat,polygon'."""
    data = _get("/compare", params={"apis": apis})
    return json.dumps(data, indent=2)


@mcp.tool()
def check_health() -> str:
    """Check OathScore service health and data freshness."""
    data = _get("/health")
    return json.dumps(data, indent=2)
