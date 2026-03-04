"""x402 micropayment support for OathScore.

Allows AI agents to pay per-request using USDC stablecoins.
No signup, no API key, no subscription — just pay and go.

Protocol: https://www.x402.org
"""

import base64
import json
import logging
import os

import httpx

logger = logging.getLogger(__name__)

# x402 configuration
X402_ENABLED = os.environ.get("X402_ENABLED", "false").lower() == "true"
X402_WALLET_ADDRESS = os.environ.get("X402_WALLET_ADDRESS", "")
X402_FACILITATOR_URL = os.environ.get("X402_FACILITATOR_URL", "https://x402.org/facilitator")
X402_NETWORK = os.environ.get("X402_NETWORK", "base-sepolia")  # base-sepolia for test, base for prod

# Pricing per request (in USDC, 6 decimals)
PRICES = {
    "now": "0.001",      # $0.001 per /now call
    "score": "0.002",    # $0.002 per /score call
    "compare": "0.005",  # $0.005 per /compare call
}


def is_enabled() -> bool:
    """Check if x402 is configured."""
    return X402_ENABLED and bool(X402_WALLET_ADDRESS)


def get_payment_required_header(endpoint: str) -> str:
    """Build the PAYMENT-REQUIRED header for a 402 response."""
    price = PRICES.get(endpoint, "0.001")
    payload = {
        "accepts": [
            {
                "scheme": "exact",
                "network": X402_NETWORK,
                "maxAmountRequired": price,
                "resource": f"https://api.oathscore.dev/{endpoint}",
                "description": f"OathScore /{endpoint} — one request",
                "mimeType": "application/json",
                "payTo": X402_WALLET_ADDRESS,
                "maxTimeoutSeconds": 60,
                "asset": "USDC",
            }
        ],
        "version": "2",
    }
    return base64.b64encode(json.dumps(payload).encode()).decode()


async def verify_payment(payment_header: str, endpoint: str) -> bool:
    """Verify a payment via the facilitator."""
    if not is_enabled():
        return False
    try:
        price = PRICES.get(endpoint, "0.001")
        resp = httpx.post(
            f"{X402_FACILITATOR_URL}/verify",
            json={
                "payload": payment_header,
                "requirements": {
                    "scheme": "exact",
                    "network": X402_NETWORK,
                    "maxAmountRequired": price,
                    "payTo": X402_WALLET_ADDRESS,
                    "asset": "USDC",
                },
            },
            timeout=10.0,
        )
        if resp.status_code == 200:
            result = resp.json()
            return result.get("valid", False)
        logger.warning("x402 verify failed: %s", resp.status_code)
        return False
    except Exception as e:
        logger.warning("x402 verify error: %s", e)
        return False


async def settle_payment(payment_header: str, endpoint: str) -> dict | None:
    """Settle a verified payment."""
    if not is_enabled():
        return None
    try:
        price = PRICES.get(endpoint, "0.001")
        resp = httpx.post(
            f"{X402_FACILITATOR_URL}/settle",
            json={
                "payload": payment_header,
                "requirements": {
                    "scheme": "exact",
                    "network": X402_NETWORK,
                    "maxAmountRequired": price,
                    "payTo": X402_WALLET_ADDRESS,
                    "asset": "USDC",
                },
            },
            timeout=15.0,
        )
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception as e:
        logger.warning("x402 settle error: %s", e)
        return None
