# RCT Platform — Constitutional AI Operating System

[![Version](https://img.shields.io/badge/version-1.0.0--alpha-blue)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)
[![CI](https://github.com/rctlabs/rct-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/rctlabs/rct-platform/actions/workflows/ci.yml)
[![Security](https://github.com/rctlabs/rct-platform/actions/workflows/security-scan.yml/badge.svg)](https://github.com/rctlabs/rct-platform/actions/workflows/security-scan.yml)

> **RCT** = Recursive Constitutional Thinking — a framework for building AI systems that can explain, verify, and govern their own reasoning.

---

## What is RCT?

RCT Platform is the open SDK layer of the RCT Ecosystem — a Constitutional AI operating system built for agentic applications that require:

- **Auditability** — every decision traces back to a signed evidence chain
- **Governance** — multi-tier consensus prevents unilateral AI action
- **Interpretability** — the FDIA equation makes intent and confidence explicit
- **Regional awareness** — built-in adapters for ASEAN, JP, KR, CN contexts

The full ecosystem runs in production at [rctlabs.co](https://rctlabs.co).  
This SDK exposes the core components under Apache 2.0.

---

## The FDIA Equation

$$F = D^I \times A$$

| Symbol | Meaning |
|--------|---------|
| **F** | Final output — the signed, consensus-approved result |
| **D** | Data quality — accuracy and completeness of inputs |
| **I** | Intent precision — how well the stated intent maps to the task |
| **A** | Alignment score — constitutional compliance coefficient (0–1) |

When A approaches 0, the system produces a **constitutional veto** rather than a hallucinated answer.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     rct-platform SDK                    │
│                                                         │
│  ┌──────────────┐  ┌───────────────┐  ┌─────────────┐  │
│  │  Intent Loop │  │   SignedAI    │  │   RCTDB     │  │
│  │  Engine      │→ │   Consensus   │→ │   Vault     │  │
│  │  (fdia.py)   │  │   (S/4/6/8)  │  │  (queries)  │  │
│  └──────────────┘  └───────────────┘  └─────────────┘  │
│          ↕                  ↕                           │
│  ┌──────────────┐  ┌───────────────┐                    │
│  │  Delta Engine│  │   Regional    │                    │
│  │  (memory_    │  │   Adapter     │                    │
│  │   delta.py)  │  │  (ASEAN+...)  │                    │
│  └──────────────┘  └───────────────┘                    │
│                                                         │
│  rct_control_plane: intent schema + DSL parser          │
└─────────────────────────────────────────────────────────┘
         ↓ 5 reference microservices ↓
   intent-loop | analysearch-intent | vector-search
         crystallizer | gateway-api
```

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/rctlabs/rct-platform.git
cd rct-platform

# 2. Install
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Edit .env with your API keys

# 4. Run tests
python -m pytest

# 5. Try the FDIA demo
python examples/hexa_core_demo.py
```

---

## Core Components

### Intent Loop Engine (`core/fdia/fdia.py`)
The FDIA Engine processes raw user intent through a 9-tier classification pipeline, assigning confidence scores and generating execution plans with full evidence chains.

```python
from core.fdia.fdia import FDIAEngine, Intent

engine = FDIAEngine()
result = engine.process(Intent(text="Analyze this dataset", context={"data": [...]}))
print(result.fdia_score)  # F = D^I × A
```

### SignedAI Consensus (`signedai/core/`)
Multi-tier verification framework for AI decisions. Supports 4-tier (S4), 6-tier (S6), and 8-tier (S8) consensus configurations.

```python
from signedai.core.models import SignedDecision
from signedai.core.router import ConsensusRouter

router = ConsensusRouter(tier=6)
decision = router.sign(output=my_ai_result, evidence=evidence_chain)
assert decision.is_constitutional()
```

### Delta Engine (`core/delta_engine/memory_delta.py`)
Efficient memory compression for long-running agentic sessions. Preserves high-signal context while applying progressive compression to older frames.

### Regional Adapter (`core/regional_adapter/regional_adapter.py`)
Context adaptation for ASEAN (TH/VN/ID/PH), Japan, South Korea, and China markets. Handles language, cultural context, and regulatory constraints.

### rct_control_plane
DSL parser and intent schema for composing complex multi-step agent pipelines:
- `intent_schema.py` — Pydantic models for intent objects
- `dsl_parser.py` — Parse RCT DSL expressions into execution graphs
- `execution_graph_ir.py` — Intermediate representation for execution plans

---

## Microservices

Five reference microservices demonstrating production patterns:

| Service | Port | Description |
|---------|------|-------------|
| `intent-loop` | 8001 | Core FDIA execution loop |
| `analysearch-intent` | 8002 | Semantic search + intent analysis |
| `vector-search` | 8003 | Vector similarity search over RCTDB |
| `crystallizer` | 8004 | Output crystallization + fact verification |
| `gateway-api` | 8000 | Unified entry point + rate limiting |

Each service includes a `Dockerfile` and follows the OpenAPI contract in `contracts/openapi.yaml`.

---

## Benchmark Results

Reproducible benchmarks are in [`benchmark/`](benchmark/).

Run against your own setup:
```bash
python benchmark/run_benchmark.py --config benchmark/default_config.json
```

See [benchmark/README.md](benchmark/README.md) for methodology.

---

## API Contract

Full OpenAPI 3.1.0 specification: [`contracts/openapi.yaml`](contracts/openapi.yaml)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health |
| `/metrics` | GET | Prometheus metrics |
| `/v1/kernel/execute` | POST | Execute RCT Kernel with intent |
| `/v1/rctdb/query` | POST | Query RCTDB knowledge vault |

---

## Whitepapers

- [Foundation (01)](docs/whitepapers/01_foundation/) — The FDIA equation, Hexagonal Core architecture, constitutional AI theory
- [Architecture (02)](docs/whitepapers/02_architecture/) — JITNA Protocol, SignedAI tier system, production deployment patterns

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Security

For vulnerability reports, see [SECURITY.md](SECURITY.md).  
Do **not** open public issues for security findings.

---

## License

Apache 2.0 — see [LICENSE](LICENSE).

Copyright 2026 RCT Labs Co., Ltd.
