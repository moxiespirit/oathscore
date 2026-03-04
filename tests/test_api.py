"""Test the OathScore API endpoints against the live deployment."""

import httpx
import json

BASE = "https://oathscore-production.up.railway.app"


def test_root():
    r = httpx.get(f"{BASE}/")
    assert r.status_code == 200
    d = r.json()
    assert d["name"] == "OathScore"
    assert "endpoints" in d


def test_now():
    r = httpx.get(f"{BASE}/now")
    assert r.status_code == 200
    d = r.json()
    assert "timestamp" in d
    assert "exchanges" in d
    assert "volatility" in d
    assert "events" in d
    assert "data_health" in d
    assert "meta" in d
    # VIX should be a number
    assert isinstance(d["volatility"]["vix"], (int, float))
    # At least some exchanges
    assert len(d["exchanges"]) >= 5


def test_health():
    r = httpx.get(f"{BASE}/health")
    assert r.status_code == 200
    d = r.json()
    assert d["status"] == "ok"


def test_scores():
    r = httpx.get(f"{BASE}/scores")
    assert r.status_code == 200
    d = r.json()
    assert "monitored_apis" in d
    assert len(d["monitored_apis"]) >= 7


def test_score_unknown():
    r = httpx.get(f"{BASE}/score/nonexistent")
    assert r.status_code == 404


def test_score_curistat():
    r = httpx.get(f"{BASE}/score/curistat")
    assert r.status_code == 200


def test_compare():
    r = httpx.get(f"{BASE}/compare", params={"apis": "curistat,polygon"})
    assert r.status_code == 200
    d = r.json()
    assert "comparison" in d


def test_compare_empty():
    r = httpx.get(f"{BASE}/compare")
    assert r.status_code == 400


def test_alerts():
    r = httpx.get(f"{BASE}/alerts")
    assert r.status_code == 200
    d = r.json()
    assert "alerts" in d
    assert "total" in d


def test_status():
    r = httpx.get(f"{BASE}/status")
    assert r.status_code == 200
    d = r.json()
    assert d["system"] == "operational"


def test_llms_txt():
    r = httpx.get(f"{BASE}/llms.txt")
    assert r.status_code == 200
    assert "OathScore" in r.text


def test_llms_full():
    r = httpx.get(f"{BASE}/llms-full.txt")
    assert r.status_code == 200
    assert "/now" in r.text


def test_robots():
    r = httpx.get(f"{BASE}/robots.txt")
    assert r.status_code == 200
    assert "Allow" in r.text


def test_ai_txt():
    r = httpx.get(f"{BASE}/ai.txt")
    assert r.status_code == 200


def test_ai_plugin():
    r = httpx.get(f"{BASE}/.well-known/ai-plugin.json")
    assert r.status_code == 200
    d = r.json()
    assert d["name_for_model"] == "oathscore"


def test_openapi():
    r = httpx.get(f"{BASE}/openapi.json")
    assert r.status_code == 200
    d = r.json()
    assert d["info"]["title"] == "OathScore"


def test_docs():
    r = httpx.get(f"{BASE}/docs")
    assert r.status_code == 200


if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed out of {len(tests)}")
