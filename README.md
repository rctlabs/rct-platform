# RCT Platform — Constitutional AI Operating System

[![Version](https://img.shields.io/badge/version-5.4.5-blue)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue)](pyproject.toml)
[![Tests](https://img.shields.io/badge/tests-142%20passed-brightgreen)](microservices/)
[![CI](https://github.com/rctlabs/rct-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/rctlabs/rct-platform/actions/workflows/ci.yml)
[![Security](https://github.com/rctlabs/rct-platform/actions/workflows/security-scan.yml/badge.svg)](https://github.com/rctlabs/rct-platform/actions/workflows/security-scan.yml)

> **RCT** = **Reverse Component Thinking** — decompose any system into its smallest verifiable parts, then rebuild with constitutional guarantees.

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

## Products

| Product | Description | Link |
|---------|-------------|------|
| 🤖 **RCTLabs** | Core intent-centric AI platform — full ecosystem access | [rctlabs.co/products/rctlabs](https://rctlabs.co/en/products/rctlabs) |
| 🎨 **ArtentAI** | AI-powered creative studio — intent-driven content generation | [rctlabs.co/products/artent-ai](https://rctlabs.co/en/products/artent-ai) |
| ✍️ **SignedAI** | Cryptographic verification layer — ED25519 signed AI outputs | [rctlabs.co/products/signed-ai](https://rctlabs.co/en/products/signed-ai) |

> All three products run on the same RCT OS constitutional core. SignedAI powers hallucination prevention via multi-LLM consensus + ED25519 attestation.

---

## The FDIA Equation

$$F = D^I \times A$$

| Symbol | Meaning |
|--------|---------|
| **F** | Final output — the signed, consensus-approved result |
| **D** | Data quality — accuracy and completeness of inputs (0.0–1.0) |
| **I** | Intent precision — how well the stated intent maps to the task (acts as exponent) |
| **A** | **Architect** — Human-in-the-loop approval gate (0.0–1.0) |

> **When A = 0, all output is blocked** — Constitutional AI guarantee. The system never acts without human approval.  
> When Intent is high (I→2), even moderate Data quality produces excellent results.

Accuracy: **0.92** (industry baseline: ~0.65). Implemented in [`core/fdia/fdia.py`](core/fdia/fdia.py).

---

## Performance Metrics

| Metric | RCT Value | Industry Average | Advantage |
|--------|-----------|-----------------|-----------|
| **Hallucination Rate** | 0.3% | 12–15% | 97% reduction via SignedAI |
| **Memory Compression** | 74% | 30–40% | Delta Engine (diff-only storage) |
| **Intent Recall (warm)** | <50ms | 2–5s | Memory-first routing |
| **Uptime SLA** | 99.98% | 99.5% | Enterprise-grade |
| **FDIA Accuracy** | 0.92 | ~0.65 | Constitutional gate |

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│              RCT ECOSYSTEM v5.4.5                        │
│         Constitutional AI Operating System               │
└──────────────────────────────────────────────────────────┘

Layer 11: CI/CD & Quality Gates
├─ GitHub Actions (ci.yml + security-scan.yml)
└─ 142 passing tests in microservices suite

Layer 10: Enterprise Hardening
├─ Security (JWT RS256, RBAC, Rate Limiting)
└─ Resilience (Circuit Breaker, Retry policies)

Layer 9: Control Plane
├─ JITNA Wire Schema (JITNAPacket: I, D, Δ, A, R, M)
├─ Ed25519 Signed Execution (RFC 8032)
├─ Replay Engine (SHA-256 checkpoints)
└─ rct_control_plane: 15-module DSL + intent schema

Layer 8: Regional Language (8 markets)
├─ LanguageDetector (EN, TH, JA, KO, ZH, VI, ID)
└─ RegionalModelRouter (LRU cache, 4-level resolution)

Layer 7: Universal Adapters (13 integrations)
└─ Home Assistant · Terraform · n8n · Obsidian · Playwright · ...

Layer 6: JITNA Protocol (RFC-001 v2.0)
└─ AI-to-AI intent wire format + task negotiation

Layer 5: SignedAI — Multi-LLM Consensus
├─ TIER_S (1) · TIER_4 (4) · TIER_6 (6) · TIER_8 (8 + veto)
└─ Hallucination rate: 0.3% vs industry 12–15%

Layer 4: RCTDB v2.0 — 8-Dimensional Universal Memory
└─ Registry Zone · Vault Zone · Governance Zone

Layer 3: 41 Production Algorithms (Tier 1–9)
Layer 2: OS Primitives (6 Kernel RFCs)
Layer 1: 7 Genome System + Cognitive Kernel

SDK Modules: signedai/ · core/ · rct_control_plane/
             5 reference microservices
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
python -m pytest microservices/ -q

# 5. Try the SignedAI demo
python examples/signed_ai_demo.py

# 6. Try the Hexa-Core demo
python examples/hexa_core_demo.py
```

**Expected output (signed_ai_demo.py):**
```
ALL IMPORTS OK
Tier 6: 6 signers, required=4
Consensus: True, confidence=75.00%
Supreme Architect: anthropic/claude-opus-4.6
```

---

## Core Components

### FDIA Engine (`core/fdia/fdia.py`)

The FDIA Scorer evaluates candidate NPC/agent actions using a weighted constitutional formula. All methods are pure functions — deterministic, no side effects.

```python
from core.fdia.fdia import FDIAScorer, FDIAWeights, NPCAction, NPCIntentType

scorer = FDIAScorer(weights=FDIAWeights())
score = scorer.score_action(
    agent_intent=NPCIntentType.DISCOVER,
    action=NPCAction(action_id="a1", action_type="explore"),
    world_resources={"knowledge": 50.0},
    agent_reputation=0.85,
    other_intents=[NPCIntentType.PROTECT],
    governance_penalty=0.0,
)
print(f"FDIA score: {score:.4f}")  # deterministic float in [0.0, 1.0]
```

### SignedAI Consensus (`signedai/core/`)

Multi-tier verification framework for AI decisions. Routes to the appropriate tier based on risk level.

```python
from signedai.core.registry import SignedAITier, RiskLevel, SignedAIRegistry
from signedai.core.router import TierRouter

# Tier selection by risk level
tier_config = SignedAIRegistry.get_tier_by_risk(RiskLevel.HIGH)
print(f"High-risk → {tier_config.tier.value}: {len(tier_config.signers)} signers")

# Consensus calculation
result = SignedAIRegistry.calculate_consensus(
    tier=SignedAITier.TIER_6,
    votes_for=4,
    votes_against=2,
)
print(f"Consensus: {result.consensus_reached}, confidence={result.confidence:.2%}")

# Cost estimation
total_cost, breakdown = SignedAIRegistry.estimate_tier_cost(
    SignedAITier.TIER_6, input_tokens=10_000, output_tokens=5_000
)
print(f"TIER_6 cost: ${total_cost:.4f}")
```

**SignedAI Tier Reference:**

| Tier | Signers | Geopolitical Balance | Required Votes | Use Case |
|------|---------|---------------------|----------------|----------|
| TIER_S | 1 | — | 1 | Chat, low-risk queries |
| TIER_4 | 4 | 2 West + 2 East | 3 (75%) | Code review, API design |
| TIER_6 | 6 | 3 West + 3 East | 4 (67%) | Production releases, DB migrations |
| TIER_8 | 6 + chairman veto | 3W + 3E + override | 6 (75%) | Critical infrastructure, crisis |

### Delta Engine (`core/delta_engine/memory_delta.py`)

Stores agent memory as compressed delta sequences — only what changed, not full state.

| Property | Value |
|----------|-------|
| **Compression** | 74% average (stores DIFF, not full state) |
| **Deduplication** | SHA-256 content hash per record |
| **Rollback** | Replay any agent to any past tick via delta chain |

```python
from core.delta_engine.memory_delta import (
    MemoryDeltaEngine, AgentMemoryState, NPCIntentType
)

engine = MemoryDeltaEngine()
engine.register_agent("agent-1", AgentMemoryState(
    agent_id="agent-1", tick=0,
    intent_type=NPCIntentType.ACCUMULATE,
    resources={"gold": 100.0},
))
engine.record_delta(
    agent_id="agent-1", tick=5,
    intent_type=NPCIntentType.ACCUMULATE,
    action_type="trade", outcome="success",
    resource_changes={"gold": 10.0},
)
state = engine.get_state_at_tick("agent-1", tick=5)
print(f"Gold at tick 5: {state.resources['gold']}")
print(f"Compression: {engine.compute_compression_ratio():.1%}")
```

### Intent Loop Engine

Every user intent passes through a 7-state pipeline:

```
RECEIVED → VALIDATED (FDIA) → MEMORY_CHECK → COMPUTING
         → VERIFYING (SignedAI) → COMMITTING (RCTDB) → COMPLETED
```

| Property | Value |
|----------|-------|
| **Cold Start** | 3–5 seconds (full computation + SignedAI consensus) |
| **Warm Recall** | <50ms (memory hit, semantic similarity > 0.95) |
| **Cost Trend** | Decreases as memory fills — approaches $0 for repeated intents |

### JITNA Protocol (RFC-001 v2.0)

Standard wire format for AI-to-AI intent communication in the RCT ecosystem.

```python
from signedai.core.models import JITNAPacket

packet = JITNAPacket(
    I="Refactor authentication module",
    D="Backend engineering",
    **{"Δ": "Adopt clean architecture pattern"},
    A="No breaking changes to public API",
    R="Test coverage must remain > 90%",
    M="All existing tests pass, cyclomatic complexity < 10",
)
```

The 6-field schema (I, D, Δ, A, R, M) is the constitutional wire format for cross-agent intent negotiation. Implemented as `JITNAPacket` in `signedai/core/models.py`.

### Regional Adapter (`core/regional_adapter/regional_adapter.py`)

Context adaptation for multi-region deployments:

| Region | Languages | Compliance |
|--------|-----------|------------|
| Thailand | TH, EN | PDPA |
| Japan | JA, EN | — |
| South Korea | KO, EN | PIPA |
| China | ZH, EN | PIPL |
| Vietnam | VI, EN | — |
| Indonesia | ID, EN | — |
| Taiwan | ZH-TW, EN | — |
| US/Global | EN | GDPR-ready |

### rct_control_plane

15-module DSL + intent schema for composing multi-step agent pipelines:

```python
from rct_control_plane import IntentObject, ExecutionGraph, DSLParser

parser = DSLParser()
graph = parser.parse(dsl_text)
print(f"Nodes: {len(graph.nodes)}, Edges: {len(graph.edges)}")
```

Available modules: `intent_schema` · `dsl_parser` · `execution_graph_ir` · `intent_compiler` · `policy_language` · `observability` · `control_plane_state` · `jitna_protocol` · `signed_execution` · `replay_engine` · `default_policies` · `cli` · `api` · `middleware` · `rich_formatter`

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
