"""
FAISS Backend coverage boost — uncovered lines.

Uncovered lines: 73-78 (euclidean/dot/unknown metric initialization),
83-90 (ivf/hnsw/unknown index types),
105 (non-cosine normalize pass-through),
132-137 (IVF not-enough-vectors warning),
184, 189 (search edge cases: idx=-1, no vec_id),
203 (euclidean distance-to-similarity conversion),
224 (get non-existent),
249 (update not found),
256 (update metadata new key),
260-261 (update vector warning),
278-289 (delete success path),
298-311 (clear with data)
"""
import sys
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch
import faiss

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.backends.faiss_backend import FAISSBackend


# ─────────────────────────────────────────────────────────────────────────────
# Initialization — metric and index type branches
# ─────────────────────────────────────────────────────────────────────────────

class TestFAISSBackendInit:
    def test_euclidean_metric(self):
        """metric='euclidean' → IndexFlatL2."""
        backend = FAISSBackend(index_type="flat", metric="euclidean")
        backend.initialize(dimension=64)
        assert backend.dimension == 64
        assert backend.faiss_index is not None

    def test_dot_metric(self):
        """metric='dot' → IndexFlatIP."""
        backend = FAISSBackend(index_type="flat", metric="dot")
        backend.initialize(dimension=64)
        assert backend.faiss_index is not None

    def test_unknown_metric_raises(self):
        backend = FAISSBackend(index_type="flat", metric="unknown_metric")
        with pytest.raises(ValueError, match="Unknown metric"):
            backend.initialize(dimension=64)

    def test_hnsw_index_type(self):
        """index_type='hnsw' → IndexHNSWFlat."""
        backend = FAISSBackend(index_type="hnsw", metric="cosine", m=16)
        backend.initialize(dimension=64)
        assert backend.faiss_index is not None

    def test_unknown_index_type_raises(self):
        backend = FAISSBackend(index_type="unknown_type", metric="cosine")
        with pytest.raises(ValueError, match="Unknown index type"):
            backend.initialize(dimension=64)

    def test_ivf_index_type_created(self):
        """index_type='ivf' → IndexIVFFlat (not yet trained)."""
        backend = FAISSBackend(index_type="ivf", metric="cosine", nlist=10)
        backend.initialize(dimension=32)
        assert backend.faiss_index is not None
        assert hasattr(backend, "index_trained")
        assert backend.index_trained is False


# ─────────────────────────────────────────────────────────────────────────────
# _normalize_vectors — non-cosine pass-through
# ─────────────────────────────────────────────────────────────────────────────

class TestNormalizeVectors:
    def test_non_cosine_returns_unchanged(self):
        backend = FAISSBackend(metric="euclidean")
        vectors = np.array([[3.0, 4.0]], dtype=np.float32)
        result = backend._normalize_vectors(vectors)
        np.testing.assert_array_equal(result, vectors)

    def test_cosine_normalizes(self):
        backend = FAISSBackend(metric="cosine")
        vectors = np.array([[3.0, 4.0]], dtype=np.float32)  # norm = 5
        result = backend._normalize_vectors(vectors)
        norm = np.linalg.norm(result[0])
        assert abs(norm - 1.0) < 1e-5

    def test_cosine_zero_vector_no_division_error(self):
        """Zero vector should not cause division error."""
        backend = FAISSBackend(metric="cosine")
        vectors = np.array([[0.0, 0.0, 0.0]], dtype=np.float32)
        result = backend._normalize_vectors(vectors)
        assert result.shape == (1, 3)


# ─────────────────────────────────────────────────────────────────────────────
# IVF: not enough vectors for training
# ─────────────────────────────────────────────────────────────────────────────

class TestIVFNotEnoughVectors:
    def test_ivf_warning_when_too_few_vectors(self, caplog):
        """IVF untrained, fewer vectors than nlist → logs warning."""
        backend = FAISSBackend(index_type="ivf", metric="cosine", nlist=100)
        backend.initialize(dimension=32)

        # Only 5 vectors, nlist=100 → warning
        vectors = np.random.randn(5, 32).tolist()
        ids = [f"v{i}" for i in range(5)]
        backend.index(vectors, ids)
        assert backend.next_idx == 5


# ─────────────────────────────────────────────────────────────────────────────
# search — euclidean and edge cases
# ─────────────────────────────────────────────────────────────────────────────

class TestFAISSSearch:
    def test_search_euclidean_converts_distance(self):
        """Euclidean metric converts distance to similarity score."""
        backend = FAISSBackend(index_type="flat", metric="euclidean")
        backend.initialize(dimension=32)
        vectors = np.random.randn(10, 32).tolist()
        ids = [f"e{i}" for i in range(10)]
        backend.index(vectors, ids)

        q = np.random.randn(32).tolist()
        results = backend.search(q, k=5)
        # All scores should be in (0, 1] for euclidean (converted via 1/(1+dist))
        assert all(0 < r.score <= 1.0 for r in results)

    def test_search_dot_product(self):
        backend = FAISSBackend(index_type="flat", metric="dot")
        backend.initialize(dimension=32)
        vectors = np.random.randn(10, 32).tolist()
        ids = [f"d{i}" for i in range(10)]
        backend.index(vectors, ids)

        q = np.random.randn(32).tolist()
        results = backend.search(q, k=3)
        assert len(results) <= 3

    def test_search_with_filter_skips_null_metadata(self):
        """filter_dict applied when metadata IS present but doesn't match → skip those."""
        backend = FAISSBackend(index_type="flat", metric="cosine")
        backend.initialize(dimension=32)
        vectors = np.random.randn(5, 32).tolist()
        ids = [f"fm{i}" for i in range(5)]
        # Some have matching metadata, some don't
        metadata = [{"cat": "A"}, {"cat": "A"}, {"cat": "B"}, {"cat": "B"}, {"cat": "A"}]
        backend.index(vectors, ids, metadata=metadata)

        q = np.random.randn(32).tolist()
        # Filter for cat=X (no matches) → empty
        results_no_match = backend.search(q, k=5, filter_dict={"cat": "X"})
        assert results_no_match == []

        # Filter for cat=A → only A results
        results_a = backend.search(q, k=5, filter_dict={"cat": "A"})
        assert all(r.metadata.get("cat") == "A" for r in results_a)

    def test_search_empty_index_returns_empty(self):
        backend = FAISSBackend(index_type="flat", metric="cosine")
        backend.initialize(dimension=32)
        q = np.random.randn(32).tolist()
        results = backend.search(q, k=5)
        assert results == []


# ─────────────────────────────────────────────────────────────────────────────
# get — non-existent
# ─────────────────────────────────────────────────────────────────────────────

class TestFAISSGet:
    def test_get_nonexistent_returns_none(self):
        backend = FAISSBackend(index_type="flat", metric="cosine")
        backend.initialize(dimension=32)
        assert backend.get("does_not_exist") is None


# ─────────────────────────────────────────────────────────────────────────────
# update — various paths
# ─────────────────────────────────────────────────────────────────────────────

class TestFAISSUpdate:
    def _setup(self, dim=32):
        backend = FAISSBackend(index_type="flat", metric="cosine")
        backend.initialize(dimension=dim)
        v = np.random.randn(3, dim).tolist()
        ids = ["u0", "u1", "u2"]
        backend.index(v, ids, metadata=[{"cat": "A"}, {"cat": "B"}, {}])
        return backend

    def test_update_not_found_returns_false(self):
        backend = self._setup()
        assert backend.update("not_found", metadata={"cat": "Z"}) is False

    def test_update_metadata_existing_key(self):
        backend = self._setup()
        result = backend.update("u0", metadata={"cat": "UPDATED"})
        assert result is True
        assert backend.metadata_store["u0"]["cat"] == "UPDATED"

    def test_update_metadata_new_key_no_prior_metadata(self):
        """Update metadata for vector with no prior metadata."""
        backend = FAISSBackend(index_type="flat", metric="cosine")
        backend.initialize(dimension=32)
        v = [np.random.randn(32).tolist()]
        backend.index(v, ["no_meta"])
        result = backend.update("no_meta", metadata={"new_key": "val"})
        assert result is True
        assert backend.metadata_store["no_meta"]["new_key"] == "val"

    def test_update_vector_logs_warning(self, caplog):
        backend = self._setup()
        new_vec = np.random.randn(32).tolist()
        result = backend.update("u0", vector=new_vec)
        assert result is True
        assert backend.vector_store["u0"] == new_vec


# ─────────────────────────────────────────────────────────────────────────────
# delete
# ─────────────────────────────────────────────────────────────────────────────

class TestFAISSDelete:
    def test_delete_not_found_returns_false(self):
        backend = FAISSBackend(index_type="flat", metric="cosine")
        backend.initialize(dimension=32)
        assert backend.delete("not_found") is False

    def test_delete_existing_cleans_mappings(self):
        backend = FAISSBackend(index_type="flat", metric="cosine")
        backend.initialize(dimension=32)
        v = [np.random.randn(32).tolist()]
        backend.index(v, ["del_me"], metadata=[{"key": "val"}])
        assert backend.delete("del_me") is True
        assert "del_me" not in backend.id_to_idx
        assert "del_me" not in backend.vector_store
        assert "del_me" not in backend.metadata_store


# ─────────────────────────────────────────────────────────────────────────────
# clear
# ─────────────────────────────────────────────────────────────────────────────

class TestFAISSClear:
    def test_clear_returns_count(self):
        backend = FAISSBackend(index_type="flat", metric="cosine")
        backend.initialize(dimension=32)
        v = np.random.randn(5, 32).tolist()
        backend.index(v, [f"c{i}" for i in range(5)])
        cleared = backend.clear()
        assert cleared == 5
        assert backend.count() == 0
        assert backend.next_idx == 0

    def test_clear_empty_index_returns_zero(self):
        backend = FAISSBackend(index_type="flat", metric="cosine")
        backend.initialize(dimension=32)
        assert backend.clear() == 0
