# Microservices Reference

Five reference microservices are included in the SDK. Each runs as a standalone FastAPI application and has a full test suite.

---

## Overview

| Microservice | Port (default) | Tests | Directory |
|-------------|---------------|-------|-----------|
| `intent-loop` | 8001 | 36 | `microservices/intent-loop/` |
| `analysearch-intent` | 8002 | 30 | `microservices/analysearch-intent/` |
| `vector-search` | 8003 | 36 | `microservices/vector-search/` |
| `crystallizer` | 8004 | 26 | `microservices/crystallizer/` |
| `gateway-api` | 8000 | 14 | `microservices/gateway-api/` |

---

## intent-loop

Stateful intent pipeline. Processes JITNAPackets through the 7-state loop.

```bash
cd microservices/intent-loop
uvicorn main:app --port 8001
```

**Key endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/intent` | POST | Submit a new intent for processing |
| `/intent/{id}` | GET | Poll intent state |
| `/health` | GET | Liveness probe |

---

## analysearch-intent

Multi-disciplinary deep analysis engine with adversarial self-refinement.

| Mode | Pipeline | Use Case |
|------|----------|---------|
| **GIGO** | GIGOProtector → validate | Garbage-in detection |
| **Mirror** | MirrorMode → reflect | Adversarial self-critique |
| **CrossDisciplinary** | Synthesis → cross-domain | Multi-field research |

```bash
cd microservices/analysearch-intent
uvicorn main:app --port 8002
```

---

## vector-search

Dual-backend semantic vector search supporting FAISS (local) and Qdrant (production).

```python
# Use FAISS for local development (no Docker needed)
from microservices.vector_search.backends import FAISSBackend

backend = FAISSBackend(dimension=384)
backend.index(vectors=embeddings, ids=doc_ids)
results = backend.search(query_vector, top_k=5)
```

```bash
cd microservices/vector-search
uvicorn main:app --port 8003
```

**Dependencies:** See `microservices/vector-search/requirements.txt` (all CVEs resolved as of v1.0.1a0).

---

## crystallizer

Concept extraction and knowledge graph builder. Converts raw text into structured concept nodes with weighted edges.

```bash
cd microservices/crystallizer
uvicorn main:app --port 8004
```

**Key operations:**
- `extract_keywords(text)` → weighted term list
- `build_concept_graph(terms)` → NetworkX graph
- `score_coherence(graph)` → float ∈ [0.0, 1.0]

---

## gateway-api

Lightweight routing gateway — CORS, request validation, health aggregation. No business logic; only routes to downstream microservices.

```bash
cd microservices/gateway-api
uvicorn main:app --port 8000
```

---

## Run All Tests

```bash
# All 142 microservice tests
pytest microservices/ -v --tb=short

# Single microservice
pytest microservices/vector-search/ -v
```
