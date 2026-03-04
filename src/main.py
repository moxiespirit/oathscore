"""OathScore API server."""

import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse

from src.aggregator import build_now_response
from src.config import NOW_REFRESH_SECONDS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# Cached /now response
_cached_response: dict | None = None
_cached_at: float = 0
_refresh_lock = asyncio.Lock()

PUBLIC_DIR = Path(__file__).parent.parent / "public"


async def _refresh_now():
    """Refresh the cached /now response."""
    global _cached_response, _cached_at
    try:
        _cached_response = await build_now_response()
        _cached_at = time.time()
        logger.info("Refreshed /now data")
    except Exception as e:
        logger.error("Failed to refresh /now: %s", e)


async def _background_refresh():
    """Background loop that refreshes /now data every N seconds."""
    while True:
        await _refresh_now()
        await asyncio.sleep(NOW_REFRESH_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background refresh on startup."""
    task = asyncio.create_task(_background_refresh())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="OathScore",
    description="Every API makes promises. OathScore checks the receipts.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/now")
async def get_now(response: Response):
    """Current world state for trading agents."""
    if _cached_response is None:
        # First request before background task completes
        async with _refresh_lock:
            if _cached_response is None:
                await _refresh_now()

    cache_age = int(time.time() - _cached_at)
    response.headers["Cache-Control"] = "public, max-age=30"
    response.headers["X-Cache-Age-Seconds"] = str(cache_age)
    response.headers["X-Next-Refresh-Seconds"] = str(max(0, NOW_REFRESH_SECONDS - cache_age))

    return _cached_response


@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "ok",
        "cached_data_age_seconds": int(time.time() - _cached_at) if _cached_at > 0 else None,
        "timestamp": datetime.now(ZoneInfo("UTC")).isoformat(),
    }


@app.get("/llms.txt")
async def llms_txt():
    """Agent-readable product description."""
    path = PUBLIC_DIR / "llms.txt"
    if path.exists():
        return PlainTextResponse(path.read_text(), media_type="text/plain")
    return PlainTextResponse("# OathScore\n> The trust layer for AI agents.", media_type="text/plain")


@app.get("/llms-full.txt")
async def llms_full_txt():
    """Comprehensive agent documentation."""
    path = PUBLIC_DIR / "llms-full.txt"
    if path.exists():
        return PlainTextResponse(path.read_text(), media_type="text/plain")
    return PlainTextResponse("# OathScore - Full Documentation\nSee /now endpoint.", media_type="text/plain")


@app.get("/robots.txt")
async def robots_txt():
    """Agent-aware robots.txt."""
    path = PUBLIC_DIR / "robots.txt"
    if path.exists():
        return PlainTextResponse(path.read_text(), media_type="text/plain")
    return PlainTextResponse("User-agent: *\nAllow: /", media_type="text/plain")


@app.get("/ai.txt")
async def ai_txt():
    """AI discovery pointer."""
    path = PUBLIC_DIR / "ai.txt"
    if path.exists():
        return PlainTextResponse(path.read_text(), media_type="text/plain")
    return PlainTextResponse("# OathScore\nAPI: /now\nDocs: /llms-full.txt", media_type="text/plain")


@app.get("/.well-known/ai-plugin.json")
async def ai_plugin():
    """ChatGPT/OpenAI plugin manifest."""
    path = PUBLIC_DIR / ".well-known" / "ai-plugin.json"
    if path.exists():
        return JSONResponse(json.loads(path.read_text()))
    return JSONResponse({"error": "not configured"}, status_code=404)
