"""Example: LangChain Agent using OathScore.

Shows how to use OathScore as tools in a LangChain agent
for market-aware reasoning.

Usage:
    pip install httpx
    python examples/langchain_agent.py
"""

import httpx

OATHSCORE_URL = "https://api.oathscore.dev"


def oathscore_now() -> str:
    """Get current world state for trading decisions.

    Returns exchange status, volatility (VIX/VVIX/SKEW),
    term structure, and upcoming economic events.
    """
    resp = httpx.get(f"{OATHSCORE_URL}/now", timeout=15)
    data = resp.json()

    vol = data.get("volatility", {})
    exchanges = data.get("exchanges", {})
    events = data.get("events", {})

    open_ex = [n for n, i in exchanges.items() if i.get("status") == "open"]

    return (
        f"VIX: {vol.get('vix', 'N/A')}, "
        f"VVIX: {vol.get('vvix', 'N/A')}, "
        f"Term: {vol.get('term_structure', 'N/A')}, "
        f"Open: {', '.join(open_ex) if open_ex else 'None'}, "
        f"Next event: {events.get('next_event', 'None')} "
        f"in {events.get('hours_until_next_event', '?')}h"
    )


def oathscore_score(api_name: str) -> str:
    """Check quality score for a financial data API.

    Returns composite score (0-100), grade, and breakdown
    for the specified API (e.g., 'polygon', 'alphavantage').
    """
    resp = httpx.get(f"{OATHSCORE_URL}/score/{api_name}", timeout=15)
    data = resp.json()
    if "composite_score" in data:
        return f"{api_name}: {data['composite_score']}/100 (grade: {data.get('grade', '?')})"
    return f"{api_name}: {data.get('status', 'unknown')} - {data.get('message', '')}"


def oathscore_compare(apis: str) -> str:
    """Compare quality scores of multiple APIs.

    Pass comma-separated names like 'polygon,alphavantage'.
    Returns side-by-side scores.
    """
    resp = httpx.get(f"{OATHSCORE_URL}/compare?apis={apis}", timeout=15)
    data = resp.json()
    results = []
    for name, info in data.get("comparison", {}).items():
        s = info.get("composite_score", "monitoring")
        results.append(f"{name}: {s}")
    return " | ".join(results) if results else "No comparison data"


def main():
    """Demo: simulate what a LangChain agent would do."""
    print("=" * 60)
    print("LangChain Agent — OathScore Tools Demo")
    print("=" * 60)

    # Step 1: Agent checks world state
    print("\n[Agent thinks] I need to check market conditions first.")
    print(f"[oathscore_now] {oathscore_now()}")

    # Step 2: Agent picks a data source
    print("\n[Agent thinks] I need market data. Let me check which source is best.")
    for api in ["polygon", "alphavantage", "finnhub", "twelvedata"]:
        print(f"[oathscore_score] {oathscore_score(api)}")

    # Step 3: Agent compares top candidates
    print("\n[Agent thinks] Let me compare the top two directly.")
    print(f"[oathscore_compare] {oathscore_compare('polygon,finnhub')}")

    # Step 4: Agent makes decision
    print("\n[Agent decides] Using the highest-scored source for trading data.")

    print("\n" + "=" * 60)
    print("In a real LangChain setup:")
    print("  tools = [oathscore_now, oathscore_score, oathscore_compare]")
    print("  agent = initialize_agent(tools, llm, agent='zero-shot-react-description')")
    print("=" * 60)


if __name__ == "__main__":
    main()
