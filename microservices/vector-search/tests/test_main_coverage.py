import asyncio
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from starlette.requests import Request

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import main


def _run(coro):
    return asyncio.run(coro)


class DummyBackend:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.initialized_dimension = None

    def initialize(self, dimension):
        self.initialized_dimension = dimension


class DummyEngine:
    def __init__(self, backend, dimension):
        self.backend = backend
        self.dimension = dimension


def test_root_endpoint_uses_environment_values(monkeypatch):
    client = TestClient(main.app)
    monkeypatch.setenv("BACKEND", "qdrant")
    monkeypatch.setenv("DIMENSION", "512")

    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["backend"] == "qdrant"
    assert response.json()["dimension"] == 512


def test_global_exception_handler_returns_error_payload():
    request = Request({"type": "http", "method": "GET", "path": "/"})

    payload = _run(main.global_exception_handler(request, RuntimeError("boom")))

    assert payload == {
        "error": "Internal server error",
        "detail": "boom",
    }


def test_lifespan_initializes_faiss_backend(monkeypatch):
    captured = {}

    monkeypatch.setenv("BACKEND", "faiss")
    monkeypatch.setenv("DIMENSION", "256")
    monkeypatch.setenv("FAISS_INDEX_TYPE", "ivf")
    monkeypatch.setenv("FAISS_METRIC", "euclidean")
    monkeypatch.setenv("FAISS_NLIST", "32")
    monkeypatch.setenv("FAISS_M", "8")
    monkeypatch.setattr(main, "FAISSBackend", DummyBackend)
    monkeypatch.setattr(main, "VectorEngine", DummyEngine)
    monkeypatch.setattr(main.routes, "set_vector_engine", lambda engine: captured.setdefault("engine", engine))

    async def exercise():
        async with main.lifespan(main.app):
            assert isinstance(main.engine, DummyEngine)
            assert main.engine.dimension == 256
            assert main.engine.backend.kwargs == {
                "index_type": "ivf",
                "metric": "euclidean",
                "nlist": 32,
                "m": 8,
            }
            assert main.engine.backend.initialized_dimension == 256
            assert captured["engine"] is main.engine

    _run(exercise())


def test_lifespan_initializes_qdrant_backend(monkeypatch):
    captured = {}

    monkeypatch.setenv("BACKEND", "qdrant")
    monkeypatch.setenv("DIMENSION", "1536")
    monkeypatch.setenv("QDRANT_URL", "http://qdrant:6333")
    monkeypatch.setenv("QDRANT_COLLECTION", "demo")
    monkeypatch.setenv("QDRANT_DISTANCE", "dot")
    monkeypatch.setattr(main, "QdrantBackend", DummyBackend)
    monkeypatch.setattr(main, "VectorEngine", DummyEngine)
    monkeypatch.setattr(main.routes, "set_vector_engine", lambda engine: captured.setdefault("engine", engine))

    async def exercise():
        async with main.lifespan(main.app):
            assert isinstance(main.engine, DummyEngine)
            assert main.engine.dimension == 1536
            assert main.engine.backend.kwargs == {
                "url": "http://qdrant:6333",
                "collection_name": "demo",
                "metric": "dot",
            }
            assert main.engine.backend.initialized_dimension == 1536
            assert captured["engine"] is main.engine

    _run(exercise())


def test_lifespan_rejects_unknown_backend(monkeypatch):
    monkeypatch.setenv("BACKEND", "mystery")

    async def exercise():
        async with main.lifespan(main.app):
            raise AssertionError("should not reach yield")

    try:
        _run(exercise())
    except ValueError as exc:
        assert "Unknown backend: mystery" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown backend")