"""OathScore API server."""

import asyncio
import json
import logging
import os
import re
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse

from src.aggregator import build_now_response
from src.billing import create_checkout_session, get_pricing, handle_webhook_event, generate_api_key, register_key, get_tier
from src.config import NOW_REFRESH_SECONDS
from src.monitor.scheduler import start_monitoring
from src.monitor.store import get_latest_scores
from src.monitor.config import MONITORED_APIS
from src.monitor.scoring import compute_score, compute_all_scores
from src.rate_limit import check_rate_limit
from src.monitor.alerts import check_alerts
from src import x402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# Cached /now response
_cached_response: dict | None = None
_cached_at: float = 0
_refresh_lock = asyncio.Lock()

PUBLIC_DIR = Path(__file__).parent.parent / "public"
DATA_DIR = Path(__file__).parent.parent / "data"
KILL_SWITCH_FILE = DATA_DIR / "kill_switch.json"

# Bot detection patterns
TRAINING_BOT_PATTERNS = re.compile(
    r"(CCBot|Google-Extended|FacebookBot|Bytespider|Amazonbot|Applebot-Extended"
    r"|cohere-ai|YouBot|anthropic-ai|Claude-Web|Diffbot|img2dataset"
    r"|ChatGPT-User|Meta-ExternalAgent|PetalBot|DataForSeoBot"
    r"|Scrapy|MJ12bot|AhrefsBot|SemrushBot|DotBot)",
    re.IGNORECASE,
)
DISCOVERY_BOT_ALLOWLIST = re.compile(
    r"(GPTBot|OAI-SearchBot|ClaudeBot|PerplexityBot|Exa|Googlebot|Bingbot)",
    re.IGNORECASE,
)
ALWAYS_ALLOW_PATHS = {"/health", "/robots.txt", "/llms.txt", "/llms-full.txt", "/ai.txt"}


def _is_killed() -> dict | None:
    """Check if kill switch is active. Returns kill state dict or None."""
    if KILL_SWITCH_FILE.exists():
        try:
            state = json.loads(KILL_SWITCH_FILE.read_text())
            if state.get("active"):
                return state
        except Exception:
            pass
    return None


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
    monitor_tasks = await start_monitoring()
    yield
    task.cancel()
    for t in monitor_tasks:
        t.cancel()
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


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log request metadata for traffic analysis (UA, path, status, latency)."""
    start = time.time()
    response = await call_next(request)
    elapsed_ms = int((time.time() - start) * 1000)
    ua = request.headers.get("user-agent", "-")
    ip = request.client.host if request.client else "-"
    logger.info("REQ %s %s %d %dms ua=%s ip=%s", request.method, request.url.path, response.status_code, elapsed_ms, ua[:120], ip)
    return response


@app.middleware("http")
async def anti_training_headers_middleware(request: Request, call_next):
    """Add anti-AI-training headers to all responses."""
    response = await call_next(request)
    response.headers["X-Robots-Tag"] = "noai, noimageai"
    response.headers["X-AI-Training"] = "disallow"
    return response


@app.middleware("http")
async def bot_detection_middleware(request: Request, call_next):
    """Block known training crawlers. Allow discovery bots and normal clients."""
    path = request.url.path
    if path in ALWAYS_ALLOW_PATHS:
        return await call_next(request)

    ua = request.headers.get("user-agent", "")
    if ua and TRAINING_BOT_PATTERNS.search(ua):
        # Allow if it's also a discovery bot (e.g. ClaudeBot vs Claude-Web)
        if not DISCOVERY_BOT_ALLOWLIST.search(ua):
            logger.info("Blocked training crawler: %s on %s", ua[:80], path)
            return JSONResponse({"error": "Forbidden", "reason": "Training crawlers are not permitted. See /robots.txt."}, status_code=403)

    return await call_next(request)


@app.middleware("http")
async def kill_switch_middleware(request: Request, call_next):
    """Emergency shutdown — returns 503 for all routes except /health when kill switch is active."""
    if request.url.path != "/health":
        kill_state = _is_killed()
        if kill_state:
            return JSONResponse(
                {"error": "Service temporarily unavailable", "reason": kill_state.get("reason", "maintenance")},
                status_code=503,
            )
    return await call_next(request)


@app.get("/")
async def root():
    """Landing page / agent entry point."""
    return {
        "name": "OathScore",
        "tagline": "Every API makes promises. OathScore checks the receipts.",
        "endpoints": {
            "world_state": "/now",
            "health": "/health",
            "docs_short": "/llms.txt",
            "docs_full": "/llms-full.txt",
            "openapi": "/openapi.json",
            "swagger": "/docs",
        },
        "github": "https://github.com/moxiespirit/oathscore",
        "usage_terms": "Use of this data for AI/ML model training is prohibited. See https://oathscore.dev/terms.",
    }


def _get_api_key(request: Request) -> str | None:
    """Extract API key from request header or query param."""
    key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
    return key


@app.get("/now")
async def get_now(request: Request, response: Response):
    """Current world state for trading agents."""
    ip = request.client.host if request.client else "unknown"
    api_key = _get_api_key(request)
    # Check for x402 payment header (bypasses rate limits)
    payment_header = request.headers.get("PAYMENT-SIGNATURE") or request.headers.get("payment-signature")
    if payment_header and x402.is_enabled():
        valid = await x402.verify_payment(payment_header, "now")
        if valid:
            settlement = await x402.settle_payment(payment_header, "now")
            response.headers["X-Payment"] = "accepted"
            # Skip rate limiting for paid requests
        else:
            return JSONResponse({"error": "Payment verification failed"}, status_code=402)
    else:
        allowed, remaining = check_rate_limit(ip, "now", api_key)
        if not allowed:
            if x402.is_enabled():
                # Offer x402 payment option
                return JSONResponse(
                    {"error": "Rate limit exceeded. Pay per request or upgrade.", "upgrade": "https://api.oathscore.dev/pricing"},
                    status_code=402,
                    headers={"PAYMENT-REQUIRED": x402.get_payment_required_header("now")},
                )
            return JSONResponse({"error": "Rate limit exceeded. Free tier: 10/day.", "upgrade": "https://api.oathscore.dev/pricing"}, status_code=429)
    response.headers["X-RateLimit-Remaining"] = str(remaining)

    if _cached_response is None:
        # First request before background task completes
        async with _refresh_lock:
            if _cached_response is None:
                await _refresh_now()

    cache_age = int(time.time() - _cached_at)
    response.headers["Cache-Control"] = "public, max-age=30"
    response.headers["X-Cache-Age-Seconds"] = str(cache_age)
    response.headers["X-Next-Refresh-Seconds"] = str(max(0, NOW_REFRESH_SECONDS - cache_age))

    if _cached_response and "usage_terms" not in _cached_response:
        _cached_response["usage_terms"] = "Use of this data for AI/ML model training is prohibited. See https://oathscore.dev/terms."

    return _cached_response


@app.get("/health")
async def health():
    """Health check. Always responds, even when kill switch is active."""
    kill_state = _is_killed()
    return {
        "status": "killed" if kill_state else "ok",
        "kill_switch": kill_state.get("reason") if kill_state else None,
        "cached_data_age_seconds": int(time.time() - _cached_at) if _cached_at > 0 else None,
        "timestamp": datetime.now(ZoneInfo("UTC")).isoformat(),
    }


@app.get("/scores")
async def scores():
    """Monitoring scores for all tracked APIs."""
    data = await get_latest_scores()
    return {
        "scores": data,
        "monitored_apis": list(MONITORED_APIS.keys()),
        "note": "Scores are preliminary. Full composite scores require 30 days of data.",
    }


@app.get("/score/{api_name}")
async def score(api_name: str):
    """Composite quality score for a specific API."""
    if api_name not in MONITORED_APIS:
        return JSONResponse({"error": f"Unknown API: {api_name}", "available": list(MONITORED_APIS.keys())}, status_code=404)
    result = compute_score(api_name)
    if not result:
        return {"api": api_name, "status": "monitoring", "message": "Not enough data yet (need 10+ pings). Check back in ~15 minutes."}
    return result


@app.get("/compare")
async def compare(apis: str = ""):
    """Side-by-side comparison of API scores."""
    if not apis:
        return JSONResponse({"error": "Provide ?apis=name1,name2", "available": list(MONITORED_APIS.keys())}, status_code=400)
    names = [a.strip() for a in apis.split(",") if a.strip()]
    unknown = [n for n in names if n not in MONITORED_APIS]
    if unknown:
        return JSONResponse({"error": f"Unknown APIs: {unknown}", "available": list(MONITORED_APIS.keys())}, status_code=404)
    results = {}
    for name in names:
        s = compute_score(name)
        results[name] = s if s else {"status": "monitoring", "message": "Not enough data yet"}
    return {"comparison": results}


@app.get("/alerts")
async def alerts():
    """Active degradation alerts for monitored APIs."""
    active = check_alerts()
    return {
        "alerts": active,
        "total": len(active),
        "high_severity": sum(1 for a in active if a.get("severity") == "high"),
    }


@app.get("/status")
async def status():
    """Full system status: monitoring summary for all APIs."""
    all_scores = compute_all_scores()
    raw = await get_latest_scores()
    return {
        "system": "operational",
        "monitored_apis": len(MONITORED_APIS),
        "apis_with_scores": len(all_scores),
        "scores": all_scores,
        "raw_metrics": raw,
        "probes": {
            "ping": {"interval_seconds": 60},
            "freshness": {"interval_seconds": 300},
            "schema": {"interval_seconds": 3600},
            "accuracy": {"interval_seconds": 3600},
            "docs": {"interval_seconds": 86400},
        },
    }


@app.get("/pricing")
async def pricing():
    """Current pricing tiers."""
    return get_pricing()


@app.post("/subscribe")
async def subscribe(request: Request):
    """Create a Stripe checkout session for a paid tier."""
    body = await request.json()
    tier = body.get("tier", "pro")
    if tier not in ("founding", "pro", "enterprise"):
        return JSONResponse({"error": "Invalid tier. Choose: founding, pro, enterprise"}, status_code=400)
    base = str(request.base_url).rstrip("/")
    result = await create_checkout_session(
        tier=tier,
        success_url=f"{base}/subscribe/success",
        cancel_url=f"{base}/pricing",
    )
    if not result:
        return JSONResponse({"error": "Billing not configured or checkout failed"}, status_code=503)
    # Pre-register the key so it's active after payment
    register_key(result["api_key"], tier)
    return {
        "checkout_url": result["checkout_url"],
        "api_key": result["api_key"],
        "important": "Save your API key NOW. It will not be shown again.",
        "tier": tier,
    }


@app.get("/subscribe/success")
async def subscribe_success(session_id: str = ""):
    """Post-checkout landing."""
    return {
        "status": "success",
        "message": "Welcome to OathScore! Your API key is now active.",
        "next_steps": [
            "Add your API key to requests: X-API-Key header or ?api_key= param",
            "Check your limits: GET /pricing",
            "Start using /now and /score endpoints",
        ],
    }


@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events with signature verification."""
    body = await request.body()
    sig = request.headers.get("stripe-signature", "")
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")

    if webhook_secret and sig:
        # Verify signature
        import hmac
        import hashlib
        timestamp = ""
        signature = ""
        for item in sig.split(","):
            k, _, v = item.partition("=")
            if k == "t":
                timestamp = v
            elif k == "v1":
                signature = v
        if timestamp and signature:
            signed_payload = f"{timestamp}.{body.decode()}"
            expected = hmac.new(webhook_secret.encode(), signed_payload.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected, signature):
                return JSONResponse({"error": "Invalid signature"}, status_code=400)
        else:
            return JSONResponse({"error": "Missing signature components"}, status_code=400)

    event = json.loads(body)
    await handle_webhook_event(event)
    return {"received": True}


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


@app.get("/terms")
async def terms():
    """Terms of Service."""
    path = PUBLIC_DIR / "terms.txt"
    if path.exists():
        return PlainTextResponse(path.read_text(), media_type="text/plain")
    return PlainTextResponse("See https://oathscore.dev/terms", media_type="text/plain")


@app.get("/ai.txt")
async def ai_txt():
    """AI discovery pointer."""
    path = PUBLIC_DIR / "ai.txt"
    if path.exists():
        return PlainTextResponse(path.read_text(), media_type="text/plain")
    return PlainTextResponse("# OathScore\nAPI: /now\nDocs: /llms-full.txt", media_type="text/plain")


@app.get("/.well-known/security.txt")
async def security_txt():
    """Security contact info (RFC 9116)."""
    path = PUBLIC_DIR / ".well-known" / "security.txt"
    if path.exists():
        return PlainTextResponse(path.read_text(), media_type="text/plain")
    return PlainTextResponse("Contact: security@oathscore.dev", media_type="text/plain")


@app.get("/.well-known/ai-plugin.json")
async def ai_plugin():
    """ChatGPT/OpenAI plugin manifest."""
    path = PUBLIC_DIR / ".well-known" / "ai-plugin.json"
    if path.exists():
        return JSONResponse(json.loads(path.read_text()))
    return JSONResponse({"error": "not configured"}, status_code=404)
