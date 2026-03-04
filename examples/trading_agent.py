"""Example: AI Trading Agent using OathScore.

This agent checks market conditions before making trading decisions.
Demonstrates how OathScore replaces 4-6 separate API calls with one.

Usage:
    pip install httpx
    python examples/trading_agent.py
"""

import httpx

OATHSCORE_URL = "https://api.oathscore.dev"
# Optional: add your API key for higher limits
# API_KEY = "os_your_key_here"
HEADERS = {}  # {"X-API-Key": API_KEY}


def get_world_state() -> dict:
    """Get current market state from OathScore — one call replaces many."""
    resp = httpx.get(f"{OATHSCORE_URL}/now", headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


def check_data_source(api_name: str) -> dict:
    """Check quality score for a data source before trusting it."""
    resp = httpx.get(f"{OATHSCORE_URL}/score/{api_name}", headers=HEADERS, timeout=15)
    if resp.status_code == 200:
        return resp.json()
    return {"error": resp.json()}


def should_trade(state: dict) -> dict:
    """Simple trading decision logic using OathScore world state."""
    exchanges = state.get("exchanges", {})
    vol = state.get("volatility", {})
    events = state.get("events", {})

    # Check if US markets are open
    cme_open = exchanges.get("CME", {}).get("is_open", False)
    nyse_open = exchanges.get("NYSE", {}).get("is_open", False)

    if not cme_open and not nyse_open:
        return {"decision": "WAIT", "reason": "US markets closed"}

    # Check volatility regime
    vix = vol.get("vix")
    if vix is None:
        return {"decision": "WAIT", "reason": "VIX data unavailable"}

    if vix > 30:
        return {"decision": "REDUCE_RISK", "reason": f"VIX elevated at {vix}"}

    # Check for imminent high-impact events
    next_event = events.get("next_event")
    if next_event:
        hours_until = events.get("hours_until_next_event", 999)
        if hours_until < 1:
            return {"decision": "WAIT", "reason": f"High-impact event imminent: {next_event}"}

    # Check term structure
    term = vol.get("term_structure")
    if term == "backwardation":
        return {"decision": "CAUTIOUS", "reason": "VIX term structure in backwardation — elevated near-term fear"}

    return {"decision": "TRADE", "reason": f"Markets open, VIX={vix}, no imminent events"}


def pick_data_source(candidates: list[str]) -> str:
    """Choose the best data source based on OathScore ratings."""
    best_name = candidates[0]
    best_score = 0

    for name in candidates:
        result = check_data_source(name)
        score = result.get("composite_score", 0)
        print(f"  {name}: OathScore {score}/100")
        if score > best_score:
            best_score = score
            best_name = name

    return best_name


def main():
    print("=" * 60)
    print("AI Trading Agent — powered by OathScore")
    print("=" * 60)

    # Step 1: Get world state (replaces 4-6 API calls)
    print("\n[1] Fetching world state...")
    state = get_world_state()

    vix = state.get("volatility", {}).get("vix", "N/A")
    exchanges = state.get("exchanges", {})
    open_exchanges = [name for name, info in exchanges.items() if info.get("status") == "open"]

    print(f"  VIX: {vix}")
    print(f"  Open exchanges: {', '.join(open_exchanges) if open_exchanges else 'None'}")
    print(f"  Term structure: {state.get('volatility', {}).get('term_structure', 'N/A')}")
    print(f"  Next event: {state.get('events', {}).get('next_event', 'None')}")

    # Step 2: Make trading decision
    print("\n[2] Evaluating trading conditions...")
    decision = should_trade(state)
    print(f"  Decision: {decision['decision']}")
    print(f"  Reason: {decision['reason']}")

    if decision["decision"] not in ("TRADE", "CAUTIOUS"):
        print("\n  Stopping here — conditions not favorable.")
        return

    # Step 3: Pick the best data source
    print("\n[3] Selecting data source...")
    candidates = ["polygon", "alphavantage", "finnhub", "twelvedata"]
    best = pick_data_source(candidates)
    print(f"\n  Selected: {best}")

    # Step 4: Execute (placeholder)
    print("\n[4] Ready to trade using", best)
    print("  (This is where your actual trading logic goes)")

    print("\n" + "=" * 60)
    print("Done. OathScore provided market context + data source selection.")


if __name__ == "__main__":
    main()
