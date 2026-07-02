from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_and_openapi() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["llm_provider"] == "DeterministicDemoLLM"
    assert client.get("/api/openapi.json").status_code == 200


def test_search_and_analysis_integration() -> None:
    search = client.get("/api/assets/search", params={"q": "0700.HK"})
    assert search.status_code == 200
    asset_id = search.json()[0]["asset_id"]
    report = client.post(
        "/api/analysis",
        json={"asset_id": asset_id, "base_currency": "USD", "locale": "zh-CN"},
    )
    assert report.status_code == 200
    payload = report.json()
    assert payload["asset"]["mic"] == "XHKG"
    assert payload["market_price"]["provenance"]["data_mode"] == "fixture"
    assert payload["fx_rate"]["as_of"] == "2025-12-31"
    assert len(payload["agents"]) == 14
    assert len(payload["debate"]) >= 4
    assert payload["llm_provider"] == "DeterministicDemoLLM"
    assert "data gaps" in payload["chair_synthesis"]


def test_rejects_ticker_only_analysis() -> None:
    response = client.post(
        "/api/analysis",
        json={"asset_id": "SAP", "base_currency": "USD", "locale": "en-US"},
    )
    assert response.status_code == 422
    assert "MIC:symbol" in response.text


def test_unsupported_asset_has_recovery_message() -> None:
    response = client.post(
        "/api/analysis",
        json={"asset_id": "XXXX:TEST", "base_currency": "USD", "locale": "en-US"},
    )
    assert response.status_code == 404
    assert "Search for a fixture-backed listing" in response.json()["detail"]
