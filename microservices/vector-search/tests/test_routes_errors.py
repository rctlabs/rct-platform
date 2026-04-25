"""
Tests for vector-search routes.py — covering error paths and all endpoints.

Uncovered lines: 61-63 (index 500), 90-97 (search 400/500), 122-129 (batch 400/500),
150-152 (health 503), 174-176 (stats 500), 195 (get 404), 202-206 (get 500),
223-253 (update 400/404/500), 268-283 (delete 404/500), 298-304 (clear 500).
"""
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from fastapi import status
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.api import routes


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures: mock engine that can be injected
# ─────────────────────────────────────────────────────────────────────────────

def make_engine(
    index_returns=None,
    search_returns=None,
    batch_search_returns=None,
    health_returns=None,
    stats_returns=None,
    get_returns=None,
    update_returns=None,
    delete_returns=None,
    clear_returns=None,
    index_raises=None,
    search_raises=None,
    batch_raises=None,
    health_raises=None,
    stats_raises=None,
    get_raises=None,
    update_raises=None,
    delete_raises=None,
    clear_raises=None,
):
    eng = MagicMock()
    if index_raises:
        eng.index.side_effect = index_raises
    else:
        eng.index.return_value = index_returns or {"indexed_count": 1, "total_vectors": 1, "time_ms": 1.0}

    if search_raises:
        eng.search.side_effect = search_raises
    else:
        eng.search.return_value = search_returns or {"results": [], "time_ms": 1.0, "total_searched": 0, "k": 10}

    if batch_raises:
        eng.batch_search.side_effect = batch_raises
    else:
        eng.batch_search.return_value = batch_search_returns or {"results": [[]], "time_ms": 1.0}

    if health_raises:
        eng.health_check.side_effect = health_raises
    else:
        eng.health_check.return_value = health_returns or {
            "status": "healthy", "vector_count": 0, "dimension": 128, "backend": "faiss"
        }

    if stats_raises:
        eng.get_stats.side_effect = stats_raises
    else:
        eng.get_stats.return_value = stats_returns or {
            "total_vectors": 0, "dimension": 128, "backend": "faiss",
            "total_searches": 0, "total_index_ops": 0, "avg_search_time_ms": 0.0,
            "avg_index_time_ms": 0.0
        }

    if get_raises:
        eng.get.side_effect = get_raises
    else:
        eng.get.return_value = get_returns

    if update_raises:
        eng.update.side_effect = update_raises
    else:
        eng.update.return_value = update_returns or {"updated": True, "vector_id": "v1"}

    if delete_raises:
        eng.delete.side_effect = delete_raises
    else:
        eng.delete.return_value = delete_returns or {"deleted": True, "vector_id": "v1"}

    if clear_raises:
        eng.clear.side_effect = clear_raises
    else:
        eng.clear.return_value = clear_returns or {"cleared_count": 0}

    return eng


@pytest.fixture(autouse=True)
def restore_vector_engine():
    """Save and restore routes.vector_engine so tests don't contaminate each other."""
    original = routes.vector_engine
    yield
    routes.vector_engine = original


def make_client(engine):
    routes.set_vector_engine(engine)
    return TestClient(app)


# ─────────────────────────────────────────────────────────────────────────────
# Index endpoint error paths
# ─────────────────────────────────────────────────────────────────────────────

class TestIndexErrors:
    def test_index_internal_error(self):
        """Engine raises generic Exception → 500."""
        client = make_client(make_engine(index_raises=Exception("disk full")))
        response = client.post("/vector/index", json={
            "vectors": [[0.1] * 128],
            "ids": ["v1"]
        })
        assert response.status_code == 500

    def test_index_value_error(self):
        """Engine raises ValueError (bad input) → 400."""
        client = make_client(make_engine(index_raises=ValueError("dimension mismatch")))
        response = client.post("/vector/index", json={
            "vectors": [[0.1] * 64],  # wrong dim
            "ids": ["v1"]
        })
        assert response.status_code == 400
        assert "dimension mismatch" in response.json()["detail"]


# ─────────────────────────────────────────────────────────────────────────────
# Search endpoint error paths
# ─────────────────────────────────────────────────────────────────────────────

class TestSearchErrors:
    def test_search_internal_error_from_engine(self):
        """Generic exception from engine → 500."""
        client = make_client(make_engine(search_raises=RuntimeError("index corrupted")))
        response = client.post("/vector/search", json={
            "query_vector": [0.1] * 128, "k": 5
        })
        assert response.status_code == 500

    def test_search_value_error_from_engine_500(self):
        """ValueError from engine → 400 (not FastAPI validation 422)."""
        client = make_client(make_engine(search_raises=ValueError("invalid k")))
        response = client.post("/vector/search", json={
            "query_vector": [0.1] * 128, "k": 5  # valid k, but engine raises ValueError
        })
        assert response.status_code == 400


# ─────────────────────────────────────────────────────────────────────────────
# Batch search error paths
# ─────────────────────────────────────────────────────────────────────────────

class TestBatchSearchErrors:
    def test_batch_value_error_400(self):
        client = make_client(make_engine(batch_raises=ValueError("bad query")))
        response = client.post("/vector/search/batch", json={
            "query_vectors": [[0.1] * 128], "k": 5
        })
        assert response.status_code == 400

    def test_batch_internal_error_500(self):
        client = make_client(make_engine(batch_raises=Exception("OOM")))
        response = client.post("/vector/search/batch", json={
            "query_vectors": [[0.1] * 128], "k": 5
        })
        assert response.status_code == 500


# ─────────────────────────────────────────────────────────────────────────────
# Health check error paths
# ─────────────────────────────────────────────────────────────────────────────

class TestHealthErrors:
    def test_health_exception_503(self):
        client = make_client(make_engine(health_raises=Exception("backend down")))
        response = client.get("/vector/health")
        assert response.status_code == 503


# ─────────────────────────────────────────────────────────────────────────────
# Stats error paths
# ─────────────────────────────────────────────────────────────────────────────

class TestStatsErrors:
    def test_stats_exception_500(self):
        client = make_client(make_engine(stats_raises=Exception("stats failed")))
        response = client.get("/vector/stats")
        assert response.status_code == 500


# ─────────────────────────────────────────────────────────────────────────────
# Get vector error paths
# ─────────────────────────────────────────────────────────────────────────────

class TestGetVectorErrors:
    def test_get_not_found_404(self):
        """Engine returns None → 404."""
        client = make_client(make_engine(get_returns=None))
        response = client.get("/vector/nonexistent_id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_exception_500(self):
        client = make_client(make_engine(get_raises=RuntimeError("index error")))
        response = client.get("/vector/some_id")
        assert response.status_code == 500


# ─────────────────────────────────────────────────────────────────────────────
# Update vector error paths
# ─────────────────────────────────────────────────────────────────────────────

class TestUpdateErrors:
    def test_update_no_payload_400(self):
        """Neither vector nor metadata provided → 400."""
        # Use a good engine (so the check is reached)
        client = make_client(make_engine())
        response = client.put("/vector/v1", json={})
        assert response.status_code == 400
        assert "Must provide" in response.json()["detail"]

    def test_update_not_found_404(self):
        """Engine returns updated=False → 404."""
        client = make_client(make_engine(update_returns={"updated": False, "vector_id": "missing"}))
        response = client.put("/vector/missing", json={"metadata": {"key": "val"}})
        assert response.status_code == 404

    def test_update_value_error_400(self):
        client = make_client(make_engine(update_raises=ValueError("bad vector")))
        response = client.put("/vector/v1", json={"metadata": {"k": "v"}})
        assert response.status_code == 400

    def test_update_exception_500(self):
        client = make_client(make_engine(update_raises=RuntimeError("write fail")))
        response = client.put("/vector/v1", json={"metadata": {"k": "v"}})
        assert response.status_code == 500

    def test_update_success_with_vector(self):
        client = make_client(make_engine(update_returns={"updated": True, "vector_id": "v1"}))
        response = client.put("/vector/v1", json={"vector": [0.5] * 128})
        assert response.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# Delete vector error paths
# ─────────────────────────────────────────────────────────────────────────────

class TestDeleteErrors:
    def test_delete_not_found_404(self):
        client = make_client(make_engine(delete_returns={"deleted": False, "vector_id": "x"}))
        response = client.delete("/vector/x")
        assert response.status_code == 404

    def test_delete_exception_500(self):
        client = make_client(make_engine(delete_raises=Exception("delete fail")))
        response = client.delete("/vector/x")
        assert response.status_code == 500


# ─────────────────────────────────────────────────────────────────────────────
# Clear endpoint error paths
# ─────────────────────────────────────────────────────────────────────────────

class TestClearErrors:
    def test_clear_exception_500(self):
        client = make_client(make_engine(clear_raises=Exception("clear fail")))
        response = client.delete("/vector/clear")
        assert response.status_code == 500
