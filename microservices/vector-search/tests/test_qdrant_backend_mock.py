"""
Mock-based tests for QdrantBackend — achieves coverage without a live Qdrant server.

Covers all major methods: initialize, index, search, get, update, delete, clear, count, get_stats
"""
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.backends.qdrant_backend import QdrantBackend
from app.core.vector_engine import SearchResult, VectorRecord


def make_mock_client():
    """Create a fully mocked QdrantClient."""
    client = MagicMock()

    # Mock get_collections
    collection_item = MagicMock()
    collection_item.name = "test_collection"
    collections_response = MagicMock()
    collections_response.collections = [collection_item]
    client.get_collections.return_value = collections_response

    # Mock search results
    hit = MagicMock()
    hit.id = "vec_001"
    hit.score = 0.95
    hit.payload = {"category": "test"}
    client.search.return_value = [hit]

    # Mock retrieve
    point = MagicMock()
    point.id = "vec_001"
    point.vector = [0.1] * 128
    point.payload = {"category": "test"}
    client.retrieve.return_value = [point]

    # Mock get_collection info
    info = MagicMock()
    info.points_count = 10
    info.indexed_vectors_count = 10
    client.get_collection.return_value = info

    return client


class TestQdrantBackendInit:
    @patch("app.backends.qdrant_backend.QdrantClient")
    def test_init_defaults(self, MockQdrantClient):
        backend = QdrantBackend()
        assert backend.url == "http://localhost:6333"
        assert backend.collection_name == "vectors"
        assert backend.metric == "cosine"
        assert backend.client is None

    @patch("app.backends.qdrant_backend.QdrantClient")
    def test_init_custom_params(self, MockQdrantClient):
        backend = QdrantBackend(
            url="http://qdrant:6333",
            collection_name="my_vecs",
            metric="euclidean"
        )
        assert backend.url == "http://qdrant:6333"
        assert backend.collection_name == "my_vecs"
        assert backend.metric == "euclidean"


class TestQdrantBackendGetDistance:
    def test_cosine_distance(self):
        backend = QdrantBackend(metric="cosine")
        from qdrant_client.models import Distance
        d = backend._get_distance()
        assert d == Distance.COSINE

    def test_euclidean_distance(self):
        backend = QdrantBackend(metric="euclidean")
        from qdrant_client.models import Distance
        d = backend._get_distance()
        assert d == Distance.EUCLID

    def test_dot_distance(self):
        backend = QdrantBackend(metric="dot")
        from qdrant_client.models import Distance
        d = backend._get_distance()
        assert d == Distance.DOT

    def test_unknown_metric_defaults_to_cosine(self):
        backend = QdrantBackend(metric="unknown")
        from qdrant_client.models import Distance
        d = backend._get_distance()
        assert d == Distance.COSINE


class TestQdrantBackendInitialize:
    @patch("app.backends.qdrant_backend.QdrantClient")
    def test_initialize_existing_collection(self, MockQdrantClient):
        mock_client = make_mock_client()
        MockQdrantClient.return_value = mock_client

        backend = QdrantBackend(collection_name="test_collection")
        backend.initialize(dimension=128)

        assert backend.dimension == 128
        assert backend.client is mock_client
        # Collection already exists — should NOT call create_collection
        mock_client.create_collection.assert_not_called()

    @patch("app.backends.qdrant_backend.QdrantClient")
    def test_initialize_creates_new_collection(self, MockQdrantClient):
        mock_client = make_mock_client()
        # Return empty collections list so creation is triggered
        empty_response = MagicMock()
        empty_response.collections = []
        mock_client.get_collections.return_value = empty_response
        MockQdrantClient.return_value = mock_client

        backend = QdrantBackend(collection_name="new_collection")
        backend.initialize(dimension=256)

        mock_client.create_collection.assert_called_once()
        assert backend.dimension == 256

    @patch("app.backends.qdrant_backend.QdrantClient")
    def test_initialize_raises_on_connection_error(self, MockQdrantClient):
        MockQdrantClient.side_effect = Exception("Connection refused")

        backend = QdrantBackend()
        with pytest.raises(Exception, match="Connection refused"):
            backend.initialize(dimension=128)


class TestQdrantBackendIndex:
    @patch("app.backends.qdrant_backend.QdrantClient")
    def test_index_vectors(self, MockQdrantClient):
        mock_client = make_mock_client()
        MockQdrantClient.return_value = mock_client

        backend = QdrantBackend()
        backend.client = mock_client
        backend.collection_name = "test"

        vectors = [[0.1] * 128, [0.2] * 128]
        ids = ["id_1", "id_2"]
        count = backend.index(vectors, ids)

        assert count == 2
        mock_client.upsert.assert_called_once()

    @patch("app.backends.qdrant_backend.QdrantClient")
    def test_index_with_metadata(self, MockQdrantClient):
        mock_client = make_mock_client()
        MockQdrantClient.return_value = mock_client

        backend = QdrantBackend()
        backend.client = mock_client
        backend.collection_name = "test"

        vectors = [[0.5] * 64]
        ids = ["meta_vec"]
        metadata = [{"label": "test"}]
        count = backend.index(vectors, ids, metadata)

        assert count == 1
        mock_client.upsert.assert_called_once()

    @patch("app.backends.qdrant_backend.QdrantClient")
    def test_index_without_metadata(self, MockQdrantClient):
        mock_client = make_mock_client()
        backend = QdrantBackend()
        backend.client = mock_client
        backend.collection_name = "col"

        vectors = [[0.3] * 32]
        ids = ["no_meta"]
        count = backend.index(vectors, ids, metadata=None)
        assert count == 1


class TestQdrantBackendSearch:
    @patch("app.backends.qdrant_backend.QdrantClient")
    def test_search_no_filter(self, MockQdrantClient):
        mock_client = make_mock_client()
        backend = QdrantBackend()
        backend.client = mock_client
        backend.collection_name = "col"

        results = backend.search([0.1] * 128, k=5)
        assert isinstance(results, list)
        assert len(results) > 0
        assert isinstance(results[0], SearchResult)

    @patch("app.backends.qdrant_backend.QdrantClient")
    def test_search_with_filter(self, MockQdrantClient):
        mock_client = make_mock_client()
        backend = QdrantBackend()
        backend.client = mock_client
        backend.collection_name = "col"

        results = backend.search([0.1] * 128, k=5, filter_dict={"category": "test"})
        assert isinstance(results, list)
        mock_client.search.assert_called_once()
        # Filter should have been passed
        call_kwargs = mock_client.search.call_args[1]
        assert call_kwargs.get("query_filter") is not None

    @patch("app.backends.qdrant_backend.QdrantClient")
    def test_search_with_null_payload(self, MockQdrantClient):
        """Test search when hit.payload is None."""
        mock_client = make_mock_client()
        # Override hit to have no payload
        hit = MagicMock()
        hit.id = "vec_null"
        hit.score = 0.80
        hit.payload = None
        mock_client.search.return_value = [hit]

        backend = QdrantBackend()
        backend.client = mock_client
        backend.collection_name = "col"

        results = backend.search([0.1] * 128, k=5)
        assert results[0].metadata is None


class TestQdrantBackendGet:
    @patch("app.backends.qdrant_backend.QdrantClient")
    def test_get_existing_vector(self, MockQdrantClient):
        mock_client = make_mock_client()
        backend = QdrantBackend()
        backend.client = mock_client
        backend.collection_name = "col"

        result = backend.get("vec_001")
        assert result is not None
        assert isinstance(result, VectorRecord)
        assert result.id == "vec_001"

    @patch("app.backends.qdrant_backend.QdrantClient")
    def test_get_nonexistent_vector_returns_none(self, MockQdrantClient):
        mock_client = make_mock_client()
        mock_client.retrieve.return_value = []

        backend = QdrantBackend()
        backend.client = mock_client
        backend.collection_name = "col"

        result = backend.get("nonexistent")
        assert result is None

    @patch("app.backends.qdrant_backend.QdrantClient")
    def test_get_on_exception_returns_none(self, MockQdrantClient):
        mock_client = make_mock_client()
        mock_client.retrieve.side_effect = Exception("Network error")

        backend = QdrantBackend()
        backend.client = mock_client
        backend.collection_name = "col"

        result = backend.get("some_id")
        assert result is None


class TestQdrantBackendUpdate:
    @patch("app.backends.qdrant_backend.QdrantClient")
    def test_update_existing_vector(self, MockQdrantClient):
        mock_client = make_mock_client()
        backend = QdrantBackend()
        backend.client = mock_client
        backend.collection_name = "col"

        success = backend.update("vec_001", metadata={"updated": True})
        assert success is True
        mock_client.upsert.assert_called()

    @patch("app.backends.qdrant_backend.QdrantClient")
    def test_update_nonexistent_returns_false(self, MockQdrantClient):
        mock_client = make_mock_client()
        mock_client.retrieve.return_value = []  # get() returns None

        backend = QdrantBackend()
        backend.client = mock_client
        backend.collection_name = "col"

        success = backend.update("nonexistent", metadata={"key": "val"})
        assert success is False

    @patch("app.backends.qdrant_backend.QdrantClient")
    def test_update_with_new_vector(self, MockQdrantClient):
        mock_client = make_mock_client()
        backend = QdrantBackend()
        backend.client = mock_client
        backend.collection_name = "col"

        new_vec = [0.9] * 128
        success = backend.update("vec_001", vector=new_vec)
        assert success is True

    @patch("app.backends.qdrant_backend.QdrantClient")
    def test_update_on_exception_returns_false(self, MockQdrantClient):
        mock_client = make_mock_client()
        mock_client.upsert.side_effect = Exception("Write error")

        backend = QdrantBackend()
        backend.client = mock_client
        backend.collection_name = "col"

        success = backend.update("vec_001", metadata={"key": "val"})
        assert success is False


class TestQdrantBackendDelete:
    @patch("app.backends.qdrant_backend.QdrantClient")
    def test_delete_existing_vector(self, MockQdrantClient):
        mock_client = make_mock_client()
        backend = QdrantBackend()
        backend.client = mock_client
        backend.collection_name = "col"

        success = backend.delete("vec_001")
        assert success is True
        mock_client.delete.assert_called_once()

    @patch("app.backends.qdrant_backend.QdrantClient")
    def test_delete_on_exception_returns_false(self, MockQdrantClient):
        mock_client = make_mock_client()
        mock_client.delete.side_effect = Exception("Delete failed")

        backend = QdrantBackend()
        backend.client = mock_client
        backend.collection_name = "col"

        success = backend.delete("vec_001")
        assert success is False


class TestQdrantBackendClear:
    @patch("app.backends.qdrant_backend.QdrantClient")
    def test_clear_collection(self, MockQdrantClient):
        mock_client = make_mock_client()
        MockQdrantClient.return_value = mock_client
        # Make get_collection return count 5 before clearing
        info = MagicMock()
        info.points_count = 5
        info.indexed_vectors_count = 5
        mock_client.get_collection.return_value = info

        backend = QdrantBackend(collection_name="test_collection")
        backend.client = mock_client
        backend.dimension = 128

        count = backend.clear()
        assert count == 5
        mock_client.delete_collection.assert_called_once()

    @patch("app.backends.qdrant_backend.QdrantClient")
    def test_clear_on_exception_returns_zero(self, MockQdrantClient):
        mock_client = make_mock_client()
        mock_client.delete_collection.side_effect = Exception("Clear failed")
        # count() depends on get_collection — must succeed first
        info = MagicMock()
        info.points_count = 3
        mock_client.get_collection.return_value = info

        backend = QdrantBackend()
        backend.client = mock_client
        backend.dimension = 128

        count = backend.clear()
        assert count == 0


class TestQdrantBackendCount:
    @patch("app.backends.qdrant_backend.QdrantClient")
    def test_count_returns_point_count(self, MockQdrantClient):
        mock_client = make_mock_client()
        info = MagicMock()
        info.points_count = 42
        mock_client.get_collection.return_value = info

        backend = QdrantBackend()
        backend.client = mock_client
        backend.collection_name = "col"

        assert backend.count() == 42

    @patch("app.backends.qdrant_backend.QdrantClient")
    def test_count_on_exception_returns_zero(self, MockQdrantClient):
        mock_client = make_mock_client()
        mock_client.get_collection.side_effect = Exception("Collection not found")

        backend = QdrantBackend()
        backend.client = mock_client
        backend.collection_name = "col"

        assert backend.count() == 0


class TestQdrantBackendGetStats:
    @patch("app.backends.qdrant_backend.QdrantClient")
    def test_get_stats_success(self, MockQdrantClient):
        mock_client = make_mock_client()
        backend = QdrantBackend(metric="cosine")
        backend.client = mock_client
        backend.collection_name = "stats_col"
        backend.dimension = 384

        stats = backend.get_stats()
        assert stats["backend"] == "qdrant"
        assert stats["collection"] == "stats_col"
        assert stats["metric"] == "cosine"
        assert stats["dimension"] == 384
        assert "points_count" in stats

    @patch("app.backends.qdrant_backend.QdrantClient")
    def test_get_stats_on_exception(self, MockQdrantClient):
        mock_client = make_mock_client()
        mock_client.get_collection.side_effect = Exception("Stats unavailable")

        backend = QdrantBackend()
        backend.client = mock_client
        backend.collection_name = "col"

        stats = backend.get_stats()
        assert stats["backend"] == "qdrant"
        assert "error" in stats
