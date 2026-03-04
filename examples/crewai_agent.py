"""Example: CrewAI Agent using OathScore MCP tools.

Shows how to connect CrewAI agents to OathScore for
market-aware decision making.

Usage:
    pip install crewai crewai-tools httpx
    python examples/crewai_agent.py
"""

import httpx

OATHSCORE_URL = "https://api.oathscore.dev"


def get_world_state() -> dict:
    """OathScore /now — full world state in one call."""
    return httpx.get(f"{OATHSCORE_URL}/now", timeout=15).json()


def get_api_score(api_name: str) -> dict:
    """OathScore quality rating for a data source."""
    resp = httpx.get(f"{OATHSCORE_URL}/score/{api_name}", timeout=15)
    return resp.json() if resp.status_code == 200 else {"error": resp.text}


def compare_apis(api_list: list[str]) -> dict:
    """Side-by-side API comparison."""
    names = ",".join(api_list)
    resp = httpx.get(f"{OATHSCORE_URL}/compare?apis={names}", timeout=15)
    return resp.json() if resp.status_code == 200 else {"error": resp.text}


def main():
    """Demonstrate OathScore tools that a CrewAI agent would use."""
    print("=" * 60)
    print("CrewAI Agent — OathScore Integration Demo")
    print("=" * 60)

    # Tool 1: get_now — world state
    print("\n[Tool: get_now] Fetching world state...")
    state = get_world_state()
    vol = state.get("volatility", {})
    exchanges = state.get("exchanges", {})
    events = state.get("events", {})

    print(f"  VIX: {vol.get('vix', 'N/A')}")
    print(f"  Term structure: {vol.get('term_structure', 'N/A')}")
    open_ex = [n for n, i in exchanges.items() if i.get("status") == "open"]
    print(f"  Open exchanges: {', '.join(open_ex) if open_ex else 'None'}")
    print(f"  Next event: {events.get('next_event', 'None')}")

    # Tool 2: get_score — individual API rating
    print("\n[Tool: get_score] Checking Polygon quality...")
    score = get_api_score("polygon")
    if "composite_score" in score:
        print(f"  Score: {score['composite_score']}/100 ({score.get('grade', '?')})")
    else:
        print(f"  Status: {score.get('status', score.get('error', 'unknown'))}")

    # Tool 3: compare_apis — side-by-side
    print("\n[Tool: compare_apis] Comparing data sources...")
    comparison = compare_apis(["polygon", "alphavantage", "finnhub"])
    for name, data in comparison.get("comparison", {}).items():
        s = data.get("composite_score", "monitoring")
        print(f"  {name}: {s}")

    # Agent decision based on all tools
    print("\n[Agent Decision]")
    vix = vol.get("vix")
    if vix and vix > 25:
        print("  HIGH VOL — reduce position sizes")
    elif not open_ex:
        print("  MARKETS CLOSED — wait for open")
    else:
        print("  CONDITIONS OK — proceed with trading plan")

    print("\n" + "=" * 60)
    print("In a real CrewAI setup, these functions become tools:")
    print('  @tool("get_world_state")')
    print('  @tool("get_api_score")')
    print('  @tool("compare_apis")')
    print("=" * 60)


if __name__ == "__main__":
    main()
