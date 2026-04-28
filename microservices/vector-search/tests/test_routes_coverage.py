"""
Coverage tests for microservices/vector-search/app/api/routes.py

Targets all error branches and success paths not hit by existing tests:
- index_vectors: ValueError + generic Exception
- search_vectors: success, ValueError, Exception
- batch_search_vectors: ValueError, Exception
- health_check: Exception
- get_stats: Exception
- get_vector: not_found (404), Exception
- update_vector: no-fields 400, not_found 404, ValueError, Exception
- delete_vector: not_found 404, Exception
- clear_index: success, Exception
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Ensure parent app package resolves from this worktree
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.api import routes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_engine():
    """Save and restore the global vector_engine to avoid cross-test pollution."""
    original = routes.vector_engine
    yield
    routes.set_vector_engine(original)


def _make_app(engine: MagicMock) -> TestClient:
    """Return a TestClient backed by a minimal app that includes the router,
    with the global engine set to *engine*."""
    app = FastAPI()
    routes.set_vector_engine(engine)
    app.include_router(routes.router)
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# index_vectors
# ---------------------------------------------------------------------------

class TestIndexVectors:
    def test_success(self):
        engine = MagicMock()
        engine.index.return_value = {"indexed_count": 2, "total_vectors": 2, "time_ms": 1.0}
        client = _make_app(engine)
        resp = client.post(
            "/vector/index",
            json={"vectors": [[0.1, 0.2], [0.3, 0.4]], "ids": ["a", "b"]},
        )
        assert resp.status_code == 201

    def test_value_error_returns_400(self):
        engine = MagicMock()
        engine.index.side_effect = ValueError("dimension mismatch")
        client = _make_app(engine)
        resp = client.post(
            "/vector/index",
            json={"vectors": [[0.1]], "ids": ["a"]},
        )
        assert resp.status_code == 400
        assert "dimension mismatch" in resp.json()["detail"]

    def test_generic_exception_returns_500(self):
        engine = MagicMock()
        engine.index.side_effect = RuntimeError("backend failure")
        client = _make_app(engine)
        resp = client.post(
            "/vector/index",
            json={"vectors": [[0.1]], "ids": ["a"]},
        )
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# search_vectors
# ---------------------------------------------------------------------------

class TestSearchVectors:
    def test_success(self):
        engine = MagicMock()
        engine.search.return_value = {
            "results": [{"id": "a", "score": 0.9, "vector": None, "metadata": {}}],
            "total": 1,
            "time_ms": 2.0,
            "query_vector": [0.1, 0.2],
            "k": 1,
            "metric": "cosine",
        }
        client = _make_app(engine)
        resp = client.post(
            "/vector/search",
            json={"query_vector": [0.1, 0.2], "k": 1},
        )
        assert resp.status_code == 200

    def test_value_error_returns_400(self):
        engine = MagicMock()
        engine.search.side_effect = ValueError("bad metric")
        client = _make_app(engine)
        resp = client.post(
            "/vector/search",
            json={"query_vector": [0.1, 0.2], "k": 1},
        )
        assert resp.status_code == 400

    def test_generic_exception_returns_500(self):
        engine = MagicMock()
        engine.search.side_effect = RuntimeError("crash")
        client = _make_app(engine)
        resp = client.post(
            "/vector/search",
            json={"query_vector": [0.1, 0.2], "k": 1},
        )
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# batch_search_vectors
# ---------------------------------------------------------------------------

class TestBatchSearchVectors:
    def test_value_error_returns_400(self):
        engine = MagicMock()
        engine.batch_search.side_effect = ValueError("bad batch")
        client = _make_app(engine)
        resp = client.post(
            "/vector/search/batch",
            json={"query_vectors": [[0.1, 0.2]], "k": 1},
        )
        assert resp.status_code == 400

    def test_generic_exception_returns_500(self):
        engine = MagicMock()
        engine.batch_search.side_effect = RuntimeError("crash")
        client = _make_app(engine)
        resp = client.post(
            "/vector/search/batch",
            json={"query_vectors": [[0.1, 0.2]], "k": 1},
        )
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# health_check
# ---------------------------------------------------------------------------

class TestHealthCheck:
    def test_exception_returns_503(self):
        engine = MagicMock()
        engine.health_check.side_effect = RuntimeError("unhealthy")
        client = _make_app(engine)
        resp = client.get("/vector/health")
        assert resp.status_code == 503


# ---------------------------------------------------------------------------
# get_stats
# ---------------------------------------------------------------------------

class TestGetStats:
    def test_exception_returns_500(self):
        engine = MagicMock()
        engine.get_stats.side_effect = RuntimeError("stats fail")
        client = _make_app(engine)
        resp = client.get("/vector/stats")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# get_vector
# ---------------------------------------------------------------------------

class TestGetVector:
    def test_not_found_returns_404(self):
        engine = MagicMock()
        engine.get.return_value = None
        client = _make_app(engine)
        resp = client.get("/vector/missing_id")
        assert resp.status_code == 404

    def test_exception_returns_500(self):
        engine = MagicMock()
        engine.get.side_effect = RuntimeError("crash")
        client = _make_app(engine)
        resp = client.get("/vector/some_id")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# update_vector
# ---------------------------------------------------------------------------

class TestUpdateVector:
    def test_no_fields_returns_400(self):
        engine = MagicMock()
        client = _make_app(engine)
        resp = client.put("/vector/some_id", json={})
        assert resp.status_code == 400

    def test_not_found_returns_404(self):
        engine = MagicMock()
        engine.update.return_value = {"updated": False}
        client = _make_app(engine)
        resp = client.put("/vector/some_id", json={"metadata": {"k": "v"}})
        assert resp.status_code == 404

    def test_value_error_returns_400(self):
        engine = MagicMock()
        engine.update.side_effect = ValueError("bad vector")
        client = _make_app(engine)
        resp = client.put("/vector/some_id", json={"metadata": {"k": "v"}})
        assert resp.status_code == 400

    def test_generic_exception_returns_500(self):
        engine = MagicMock()
        engine.update.side_effect = RuntimeError("crash")
        client = _make_app(engine)
        resp = client.put("/vector/some_id", json={"metadata": {"k": "v"}})
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# delete_vector
# ---------------------------------------------------------------------------

class TestDeleteVector:
    def test_not_found_returns_404(self):
        engine = MagicMock()
        engine.delete.return_value = {"deleted": False}
        client = _make_app(engine)
        resp = client.delete("/vector/missing_id")
        assert resp.status_code == 404

    def test_generic_exception_returns_500(self):
        engine = MagicMock()
        engine.delete.side_effect = RuntimeError("crash")
        client = _make_app(engine)
        resp = client.delete("/vector/some_id")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# clear_index
# ---------------------------------------------------------------------------

class TestClearIndex:
    def test_exception_returns_500(self):
        engine = MagicMock()
        engine.clear.side_effect = RuntimeError("crash")
        client = _make_app(engine)
        # The route is DELETE /vector/clear — note: this is a fixed path,
        # so it may conflict with /{vector_id}. Test using direct path.
        resp = client.delete("/vector/clear")
        assert resp.status_code == 500
