# RCT Platform — Public SDK Testing Canonical

**Version:** 1.0.1a0  
**Last Updated:** 2026-04-17  
**Total SDK Tests:** 591 passed · 0 failed · 89% coverage  
**CI Status:** [![CI](https://github.com/rctlabs/rct-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/rctlabs/rct-platform/actions/workflows/ci.yml)

---

## 1. Test Matrix

This matrix tracks the reference microservice slice of the SDK test suite. The
repository-wide total shown above also includes tests under `core/tests`,
`signedai/tests`, `rct_control_plane/tests`, and top-level `tests/`.

| Microservice | Test File(s) | Tests | Scope |
|---|---|---|---|
| `analysearch-intent` | `test_analysearch_engine.py` | 30 | GIGOProtector, MirrorMode, CrossDisciplinarySynthesis |
| `intent-loop` | `test_intent_loop.py`, `test_intent_loop_extended.py` | 36 | IntentState, JITNAPacket, IntentLoopEngine, FDIA gating |
| `gateway-api` | `test_gateway_api.py` | 14 | Health endpoints, routing, CORS, JSON responses |
| `vector-search` | `test_vector.py`, `test_vector_extended.py` | 36 | FAISSBackend, QdrantBackend, VectorEngine, API endpoints |
| `crystallizer` | `test_crystallizer.py` | 26 | Keyword extraction, concept graph, scoring |
| **TOTAL** | | **142** | |

---

## 2. Python Version Matrix

Tests pass on all three supported versions:

| Python | CI Status |
|---|---|
| 3.10 | ✅ |
| 3.11 | ✅ (coverage upload) |
| 3.12 | ✅ |

---

## 3. How to Run Tests Locally

### Prerequisites

```bash
git clone https://github.com/rctlabs/rct-platform.git
cd rct-platform
pip install -r requirements.txt
pip install pytest pytest-cov
```

### Run all SDK tests (all 5 microservices)

```bash
pytest microservices/ -v
```

### Run with coverage report

```bash
pytest microservices/ --cov=microservices --cov-report=term-missing -v
```

### Run a single microservice

```bash
pytest microservices/intent-loop/ -v
pytest microservices/analysearch-intent/ -v
pytest microservices/vector-search/ -v
pytest microservices/gateway-api/ -v
pytest microservices/crystallizer/ -v
```

### Run with importlib mode (recommended for module isolation)

```bash
pytest --import-mode=importlib microservices/ -v
```

---

## 4. Test Coverage Notes

| Scope | Covered by tests | Not yet covered |
|---|---|---|
| FDIA engine (`core/fdia/`) | ✅ via intent-loop tests | Direct unit tests TBD |
| SignedAI registry (`signedai/core/`) | ✅ via examples; no formal test suite yet | Formal test suite in roadmap |
| Control plane DSL parser | ✅ via gateway-api tests | Edge case coverage TBD |
| Control plane state machine | ⚠️ no dedicated tests yet | Planned for v1.1.0-alpha |
| Genome API (`microservices/gateway-api/genome_api.py`) | ✅ 501 stubs — enterprise module only | Full tests available in enterprise runtime |

---

## 5. Scope Boundary

These 142 microservice tests are one subset of the **public SDK layer** test suite:

- ✅ 5 reference microservices
- ✅ Core SDK modules (FDIA, SignedAI, control plane objects)

**Not included in this public test suite:**
- Private enterprise runtime (62 microservices, 4,849+ tests in v5.4.5)
- Dashboard frontend
- Infrastructure / k8s / Docker stack

---

## 6. Security & Quality Gates (CI)

| Gate | Tool | Threshold |
|---|---|---|
| Tests | pytest | Repository CI must stay green across the full SDK suite |
| Type check | mypy | Errors fail the build |
| SAST | bandit | HIGH severity findings fail the build |
| Secret scan | gitleaks | Any real credential fails the build |
| CVE scan | pip-audit | Reported as advisory (upgrade backlog managed separately) |

See `.github/workflows/ci.yml` and `.github/workflows/security-scan.yml` for full configuration.
