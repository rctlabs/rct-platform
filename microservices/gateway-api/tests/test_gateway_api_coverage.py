import asyncio
import json
import os
import sys
from types import SimpleNamespace

from fastapi.testclient import TestClient
from starlette.requests import Request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import gateway_main


def _run(coro):
    return asyncio.run(coro)


def test_load_stats_cache_returns_baseline_when_file_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(gateway_main, "_STATS_CACHE_PATH", str(tmp_path / "missing.json"))

    stats = gateway_main._load_stats_cache()

    assert stats["source"] == "baseline"
    assert stats["testCount"] == gateway_main._BASELINE_STATS["testCount"]


def test_load_stats_cache_returns_cached_values_for_fresh_file(monkeypatch, tmp_path):
    cache_path = tmp_path / "stats.json"
    cache_path.write_text(json.dumps({"testCount": 9999, "algorithmCount": 77}), encoding="utf-8")
    monkeypatch.setattr(gateway_main, "_STATS_CACHE_PATH", str(cache_path))

    stats = gateway_main._load_stats_cache()

    assert stats["source"] == "cache"
    assert stats["testCount"] == 9999
    assert stats["algorithmCount"] == 77
    assert stats["microserviceCount"] == gateway_main._BASELINE_STATS["microserviceCount"]


def test_load_stats_cache_falls_back_for_stale_or_invalid_file(monkeypatch, tmp_path):
    cache_path = tmp_path / "stats.json"
    cache_path.write_text("{not-valid-json", encoding="utf-8")
    monkeypatch.setattr(gateway_main, "_STATS_CACHE_PATH", str(cache_path))
    monkeypatch.setattr(gateway_main.os.path, "getmtime", lambda _: 0)

    stats = gateway_main._load_stats_cache()

    assert stats["source"] == "baseline"
    assert stats["testCount"] == gateway_main._BASELINE_STATS["testCount"]


def test_stats_endpoint_merges_live_fields(monkeypatch):
    client = TestClient(gateway_main.app)
    monkeypatch.setattr(gateway_main, "_load_stats_cache", lambda: {
        "testCount": 7000,
        "microserviceCount": 80,
        "algorithmCount": 50,
        "source": "cache",
    })

    response = client.get("/rctlabs/system/stats")
    payload = response.json()

    assert response.status_code == 200
    assert payload["testCount"] == 7000
    assert payload["microserviceCount"] == 80
    assert payload["algorithmCount"] == 50
    assert payload["source"] == "cache"
    assert payload["layerCount"] == 10
    assert payload["version"] == gateway_main.app.version


def test_benchmark_summary_endpoint_returns_expected_sections():
    client = TestClient(gateway_main.app)

    response = client.get("/rctlabs/benchmark/summary")
    payload = response.json()

    assert response.status_code == 200
    assert len(payload["radarData"]) == 6
    assert len(payload["barData"]) == 6
    assert len(payload["counterStats"]) == 4
    assert payload["version"] == gateway_main.app.version


def test_health_check_reports_healthy_services(monkeypatch):
    fake_module = SimpleNamespace(get_manager=lambda: object())
    monkeypatch.setitem(sys.modules, "genome_api", fake_module)
    monkeypatch.setattr(gateway_main, "genome_available", True)
    monkeypatch.setattr(gateway_main, "signedai_available", True)

    payload = _run(gateway_main.health_check())

    assert payload["gateway"] == "healthy"
    assert payload["services"]["genome"]["status"] == "healthy"
    assert payload["services"]["signedai"]["status"] == "healthy"


def test_health_check_reports_degraded_genome(monkeypatch):
    def _boom():
        raise RuntimeError("manager down")

    fake_module = SimpleNamespace(get_manager=_boom)
    monkeypatch.setitem(sys.modules, "genome_api", fake_module)
    monkeypatch.setattr(gateway_main, "genome_available", True)
    monkeypatch.setattr(gateway_main, "signedai_available", False)

    payload = _run(gateway_main.health_check())

    assert payload["services"]["genome"]["status"] == "degraded"
    assert "manager down" in payload["services"]["genome"]["error"]
    assert payload["services"]["signedai"]["status"] == "unavailable"


def test_health_check_reports_unavailable_services(monkeypatch):
    monkeypatch.setattr(gateway_main, "genome_available", False)
    monkeypatch.setattr(gateway_main, "signedai_available", False)

    payload = _run(gateway_main.health_check())

    assert payload["services"]["genome"]["status"] == "unavailable"
    assert payload["services"]["signedai"]["status"] == "unavailable"


def test_not_found_handler_returns_json_response():
    request = Request({"type": "http", "method": "GET", "path": "/missing", "headers": []})

    response = _run(gateway_main.not_found_handler(request, RuntimeError("missing")))

    assert response.status_code == 404
    assert b"/missing" in response.body
    assert b"available_endpoints" in response.body


def test_server_error_handler_returns_json_response():
    request = Request({"type": "http", "method": "GET", "path": "/error", "headers": []})

    response = _run(gateway_main.server_error_handler(request, RuntimeError("kaput")))

    assert response.status_code == 500
    assert b"Internal Server Error" in response.body
    assert b"kaput" in response.body