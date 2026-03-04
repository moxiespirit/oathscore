"""Stripe billing + API key management for OathScore."""

import hashlib
import logging
import os
import secrets
import time

import httpx

logger = logging.getLogger(__name__)

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_BASE = "https://api.stripe.com/v1"

# In-memory API key store (boot from Supabase, write-through)
# key_hash -> {tier, stripe_customer_id, stripe_subscription_id, created_at}
_keys: dict[str, dict] = {}

PRICE_IDS = {
    "founding": os.environ.get("STRIPE_PRICE_FOUNDING"),
    "pro": os.environ.get("STRIPE_PRICE_PRO"),
    "enterprise": os.environ.get("STRIPE_PRICE_ENTERPRISE"),
}


def _stripe(method: str, path: str, data: dict | None = None) -> dict | None:
    """Make a Stripe API call."""
    if not STRIPE_SECRET_KEY:
        logger.warning("Stripe not configured")
        return None
    try:
        resp = httpx.request(
            method,
            f"{STRIPE_BASE}{path}",
            data=data,
            auth=(STRIPE_SECRET_KEY, ""),
            timeout=15.0,
        )
        if resp.status_code in (200, 201):
            return resp.json()
        logger.warning("Stripe %s %s: %s %s", method, path, resp.status_code, resp.text[:200])
        return None
    except Exception as e:
        logger.warning("Stripe error: %s", e)
        return None


def _hash_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_api_key() -> str:
    """Generate a new API key."""
    return f"os_{secrets.token_hex(24)}"


def register_key(api_key: str, tier: str, customer_id: str = "", subscription_id: str = ""):
    """Register an API key in memory."""
    from src.rate_limit import register_key as rl_register
    h = _hash_key(api_key)
    _keys[h] = {
        "tier": tier,
        "stripe_customer_id": customer_id,
        "stripe_subscription_id": subscription_id,
        "created_at": time.time(),
    }
    rl_register(api_key, tier)


def validate_key(api_key: str) -> dict | None:
    """Look up an API key. Returns key info or None."""
    h = _hash_key(api_key)
    return _keys.get(h)


def get_tier(api_key: str) -> str:
    """Get the tier for an API key."""
    info = validate_key(api_key)
    return info["tier"] if info else "free"


async def create_checkout_session(tier: str, success_url: str, cancel_url: str) -> dict | None:
    """Create a Stripe Checkout session for a subscription."""
    price_id = PRICE_IDS.get(tier)
    if not price_id:
        logger.warning("No price ID for tier: %s", tier)
        return None

    # Generate the API key upfront, pass in metadata
    api_key = generate_api_key()

    result = _stripe("POST", "/checkout/sessions", {
        "mode": "subscription",
        "line_items[0][price]": price_id,
        "line_items[0][quantity]": "1",
        "success_url": success_url + "?session_id={CHECKOUT_SESSION_ID}",
        "cancel_url": cancel_url,
        "metadata[tier]": tier,
        "metadata[api_key_hash]": _hash_key(api_key),
        "subscription_data[metadata][tier]": tier,
        "subscription_data[metadata][api_key_hash]": _hash_key(api_key),
    })

    if result:
        return {
            "checkout_url": result.get("url"),
            "session_id": result.get("id"),
            "api_key": api_key,  # Show once, user must save it
        }
    return None


async def handle_webhook_event(event: dict):
    """Process Stripe webhook events."""
    event_type = event.get("type")
    data = event.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed":
        meta = data.get("metadata", {})
        tier = meta.get("tier", "pro")
        key_hash = meta.get("api_key_hash")
        customer_id = data.get("customer", "")
        subscription_id = data.get("subscription", "")

        if key_hash and key_hash in _keys:
            _keys[key_hash]["stripe_customer_id"] = customer_id
            _keys[key_hash]["stripe_subscription_id"] = subscription_id
            logger.info("Checkout completed for tier=%s customer=%s", tier, customer_id)

    elif event_type == "customer.subscription.deleted":
        # Subscription cancelled — downgrade to free
        sub_id = data.get("id")
        for h, info in _keys.items():
            if info.get("stripe_subscription_id") == sub_id:
                info["tier"] = "free"
                logger.info("Subscription cancelled, downgraded key to free: %s", h[:8])
                break

    elif event_type == "invoice.payment_failed":
        customer_id = data.get("customer")
        logger.warning("Payment failed for customer: %s", customer_id)


def get_pricing() -> dict:
    """Return current pricing tiers."""
    return {
        "tiers": {
            "free": {
                "price": "$0/mo",
                "limits": {"now": "10/day", "score": "5/day", "compare": "2/day"},
                "features": ["Basic world state", "Limited score queries"],
            },
            "founding": {
                "price": "$9/mo (lifetime — first 50 subscribers)",
                "limits": {"now": "5,000/day", "score": "2,500/day", "compare": "500/day"},
                "features": ["Full world state", "All score queries", "Priority support", "Locked-in rate forever"],
                "slots_remaining": max(0, 50 - _count_tier("founding")),
            },
            "pro": {
                "price": "$29/mo",
                "limits": {"now": "10,000/day", "score": "5,000/day", "compare": "1,000/day"},
                "features": ["Full world state", "All score queries", "Webhook alerts", "API comparison reports"],
            },
            "enterprise": {
                "price": "$99/mo",
                "limits": {"now": "100,000/day", "score": "50,000/day", "compare": "5,000/day"},
                "features": ["Everything in Pro", "Dedicated support", "Custom monitoring", "SLA guarantee"],
            },
        },
        "founding_note": "Founding tier locks in $9/mo for life. Limited to first 50 subscribers.",
    }


def _count_tier(tier: str) -> int:
    """Count active subscriptions at a tier."""
    return sum(1 for info in _keys.values() if info.get("tier") == tier)
