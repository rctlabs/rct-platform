# RCT Platform — Intent-Centric AI Operating System

[![CI](https://github.com/rctlabs/rct-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/rctlabs/rct-platform/actions/workflows/ci.yml)
[![Security](https://github.com/rctlabs/rct-platform/actions/workflows/security-scan.yml/badge.svg)](https://github.com/rctlabs/rct-platform/actions/workflows/security-scan.yml)
[![codecov](https://codecov.io/gh/rctlabs/rct-platform/graph/badge.svg?token=IE08MVKA6C)](https://app.codecov.io/gh/rctlabs/rct-platform)
[![Version](https://img.shields.io/badge/version-1.0.1a0-blue)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Status](https://img.shields.io/badge/status-PUBLIC%20ALPHA-orange)](CHANGELOG.md)
[![Website](https://img.shields.io/badge/website-rctlabs.co-brightgreen)](https://rctlabs.co)

## Intent-Centric AI Operating System — Constitutional Architecture

> **RCT** = **Reverse Component Thinking** — decompose any system into its smallest verifiable parts, then rebuild with constitutional guarantees.

---

## What is RCT?

**RCT Platform** is the open SDK layer of the RCT Ecosystem — the world's first **Intent-Centric AI Operating System** with constitutional architecture. Think of it as **"Linux for AI Agents."** It provides:

- **Auditability** — every decision traces back to a signed evidence chain
- **Governance** — multi-tier consensus prevents unilateral AI action  
- **Interpretability** — the FDIA equation makes intent and confidence explicit
- **Regional awareness** — built-in adapters for ASEAN, JP, KR, CN contexts

The full ecosystem runs in production at [rctlabs.co](https://rctlabs.co).  
This SDK exposes the core components under Apache 2.0.

🌐 **Website:** [rctlabs.co](https://rctlabs.co) · 🔗 **GitHub:** [github.com/rctlabs](https://github.com/rctlabs)

---

## What's Included in This SDK

| Component | In This SDK (Apache 2.0) | Enterprise Only (Proprietary) |
|-----------|--------------------------|-------------------------------|
| FDIA Scorer + equation engine | ✅ `core/fdia/fdia.py` | — |
| SignedAI multi-LLM consensus | ✅ `signedai/core/` | — |
| HexaCore 7-model registry | ✅ `signedai/core/registry.py` | — |
| Delta Engine (74% compression) | ✅ `core/delta_engine/` | — |
| Regional Language Adapter | ✅ `core/regional_adapter/` | — |
| RCT Control Plane DSL | ✅ `rct_control_plane/` (15 modules) | — |
| 5 Reference Microservices | ✅ `microservices/` (142 tests) | — |
| CLI (`rct` entry point) | ✅ `pip install -e .` | — |
| Genome / Creator Profile API | ❌ 501 stub (`genome_api.py`) | ✅ Full implementation |
| Full Production Microservice Stack | ❌ | ✅ 62 microservices |
| Enterprise Dashboard | ❌ | ✅ |
| Docker Compose + full infra | ❌ | ✅ |
| 8-level test pyramid (4,849 tests) | ❌ | ✅ private |

> **SDK alpha** means: API may change without backward-compatibility notice before v1.0.0 stable.  
> **Enterprise** means: runs at [rctlabs.co](https://rctlabs.co) — contact for licensing.

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
| **F** | **Future** — the desired output the AI must deliver |
| **D** | Data quality — accuracy and completeness of inputs (0.0–1.0) |
| **I** | Intent precision — clarity of intent acts as an **exponent** (higher = amplifies result) |
| **A** | **Architect** — Human-in-the-loop approval gate (0.0–1.0) |

> **When Intent is high (I→2), even moderate Data quality produces excellent results.**  
> **When A = 0, all output is blocked** — Constitutional AI guarantee. The system never acts without human approval.

Accuracy: **0.92** (industry baseline: ~0.65). Implemented in [`core/fdia/fdia.py`](core/fdia/fdia.py).

---

## Key Numbers

| Metric | Value |
|--------|-------|
| **SDK Tests (this repo)** | 591 passed · 0 failed · 89% coverage — full SDK test suite |
| **Algorithms** | 41 (Tier 1–9, reference implementations) |
| **LLM Models** | 7 HexaCore (3 Western + 3 Eastern + 1 Regional Thai) |
| **Hallucination Rate** | 0.3% (vs industry 12–15%) — 97% reduction via SignedAI |
| **Memory Compression** | 74% via Delta Engine (stores state diffs, not full state) |
| **Intent Recall Speed** | Cold start 3–5s → Warm recall <50ms (Intent Loop) |
| **Uptime SLA** | 99.98% |
| **Languages** | 8 regional pairs (JP, KR, CN, TW, TH, VN, ID, US) |
| **Universal Adapters** | 13 (Home Assistant, Terraform, n8n, Obsidian, Playwright, ...) |
| **FDIA Accuracy** | 0.92 (industry baseline: ~0.65) |

> **591 tests** currently pass across the public SDK suite. Of these, **142 tests**
> cover the 5 reference microservices directly.

---

## Architecture

```text
┌──────────────────────────────────────────────────────────┐
│               RCT PLATFORM SDK v1.0.1a0                  │
│         Intent-Centric AI Operating System               │
└──────────────────────────────────────────────────────────┘

Layer 11: CI/CD & Quality Gates
├─ GitHub Actions (ci.yml + security-scan.yml)
├─ 591 passing tests · 89% coverage · Python 3.10/3.11/3.12
└─ E2E integration tests (no Docker required)

Layer 10: Enterprise Hardening
├─ Security (JWT RS256, RBAC, ABAC, Rate Limiting)
├─ Validation (SQL Injection 3-layer, Pydantic v2, XSS)
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

> **Enterprise layer** (62 microservices, proprietary) runs in production at [rctlabs.co](https://rctlabs.co).

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

### Analysearch Intent (`microservices/analysearch-intent/`)

Multi-disciplinary deep analysis engine with adversarial self-refinement:

| Mode | Pipeline | Use Case |
|------|----------|----------|
| `quick` | Single-pass lookup | Fast factual queries |
| `standard` | Analysis + research synthesis | Standard decisions |
| `deep` | Mirror Mode (3 passes) | Critical analysis |
| `mirror` | PROPOSE → COUNTER → REFINE loop | Adversarial self-challenge |

Key capabilities:
- **GIGO Protection** — Entropy-based input validation; garbage in = rejected before any LLM call
- **Golden Keyword Crystallization** — ALGO-41 extracts the 3–5 decisive keywords from any query
- **Cross-Disciplinary Synthesis** — Connects insights across unrelated domains automatically
- **Intent Conservation** — Original intent preserved and checked through every refinement pass

### Hexa-Core Registry (`signedai/core/registry.py`)

7 purpose-specific AI models with full geopolitical balance:

| Role | Model | Country | Specialty |
|------|-------|---------|-----------|
| SUPREME_ARCHITECT | claude-opus-4.6 | US | Architecture, reasoning, final decisions |
| LEAD_BUILDER | kimi-k2.5 | CN | Complex coding, visual analysis |
| JUNIOR_BUILDER | minimax-m2.1 | CN | Routine coding, unit tests |
| SPECIALIST | gemini-3-flash | US | Finance, health, multimodal, speed |
| LIBRARIAN | grok-4.1-fast | US | Long context (2M tokens), RAG, science |
| HUMANIZER | deepseek-v3.2 | CN | Natural language, creative, translation |
| **REGIONAL_THAI** | **typhoon-v2-70b** | **TH** | **Thai NLP, Thai legal/finance (native quality)** |

```python
from signedai.core.registry import HexaCoreRegistry, HexaCoreRole

# All 7 models
for role, model in HexaCoreRegistry.MODELS.items():
    print(f"{role.value}: {model.id} ({model.country})")

# Geopolitical balance
balance = HexaCoreRegistry.get_geopolitical_balance()
# → {'US': 3, 'CN': 3, 'TH': 1}

# Thai specialist
thai = HexaCoreRegistry.get_model(HexaCoreRole.REGIONAL_THAI)
print(thai.specialties)  # ['Thai NLP', 'Thai culture', 'Thai legal', ...]

# Filter by region
thai_models = HexaCoreRegistry.get_models_by_country("TH")
```

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

## Enterprise Platform Milestone — v5.4.5 (Private)

> **Note:** This section records the private enterprise platform history. The public SDK versioning starts at `v1.0.0-alpha`. See [CHANGELOG.md](CHANGELOG.md) for SDK release notes.

✅ **4,849 Passed · 16 Skipped · 0 Failed · 0 Errors** — Complete private enterprise test suite (all 62 microservices)  
✅ **asyncio Modernization** — Python 3.12 compatible, removed all deprecated `event_loop` fixtures  
✅ **Pydantic Field Ordering Fix** — `VerificationBlock` validator ordering resolved  
✅ **Module Isolation** — Resolved `app/` namespace collision across 9 microservices  
✅ **Policy Engine Fix** — `asyncio.get_running_loop()` with safe fallback  
✅ **REGIONAL_THAI Model** — Typhoon v2 70B (SCB10X) added as 7th HexaCore model  

Full SDK changelog → [CHANGELOG.md](CHANGELOG.md)

---

## Whitepapers

- [Foundation (01)](docs/whitepapers/01_foundation/) — The FDIA equation, Hexagonal Core architecture, constitutional AI theory
- [Architecture (02)](docs/whitepapers/02_architecture/) — JITNA Protocol, SignedAI tier system, production deployment patterns

---

## Project Structure

```
rct-platform/
├─ core/                        # Core algorithms + AI engine
│  ├─ fdia/fdia.py              # FDIA Scorer (NPCIntentType, FDIAWeights)
│  ├─ delta_engine/             # Memory Delta Engine (74% compression)
│  └─ regional_adapter/         # 8-market language routing
├─ signedai/                    # SignedAI consensus framework
│  └─ core/
│     ├─ registry.py            # HexaCoreRegistry (7 models) + SignedAIRegistry
│     ├─ router.py              # TierRouter (risk → tier selection)
│     └─ models.py              # JITNAPacket, AnalysisJob
├─ rct_control_plane/           # 15-module DSL + intent schema
├─ microservices/               # 5 reference microservices
│  ├─ intent-loop/              # Core FDIA execution loop (port 8001)
│  ├─ analysearch-intent/       # Deep analysis + Mirror Mode (port 8002)
│  ├─ vector-search/            # RCTDB semantic search (port 8003)
│  ├─ crystallizer/             # Output crystallization (port 8004)
│  └─ gateway-api/              # Unified entry + rate limiting (port 8000)
├─ examples/                    # Working code demos
│  ├─ signed_ai_demo.py         # SignedAI imports + consensus demo
│  └─ hexa_core_demo.py         # All 7 models + geopolitical balance
├─ contracts/openapi.yaml       # OpenAPI 3.1.0 spec
└─ docs/                        # Architecture docs + whitepapers
```

---

## Built With

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?logo=pydantic&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![pytest](https://img.shields.io/badge/pytest-0A9EDC?logo=pytest&logoColor=white)

---

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

- 🐛 [Report Bugs](https://github.com/rctlabs/rct-platform/issues)
- 💡 [Suggest Features](https://github.com/rctlabs/rct-platform/discussions)
- 📖 Improve docs
- 🧪 Add tests
- 🔌 Build adapters for new integrations

---

## Security

For vulnerability reports, see [SECURITY.md](SECURITY.md).  
Do **not** open public issues for security findings.

---

## 👤 Creator

**Ittirit Saengow (อิทธิฤทธิ์ แซ่โง้ว)**  
*Architect & Sole Creator of RCT Platform and the RCT Ecosystem*

Built the entire RCT Ecosystem independently — from the FDIA equation through 591 tests, Constitutional AI architecture, SignedAI multi-LLM consensus, and this open SDK. A Thai developer building trust-layer AI infrastructure for the Intelligence Age.

| | |
|---|---|
| **GitHub** | [@ittirit720](https://github.com/ittirit720) |
| **Email** | ittirit720@gmail.com |
| **Org** | founder@rctlabs.co |
| **Website** | [rctlabs.co](https://rctlabs.co) |
| **Location** | Bangkok, Thailand 🇹🇭 |

> *"Design the system so it cannot misbehave — not just configure it to be safe."*

---

## License

Apache 2.0 — see [LICENSE](LICENSE).

Copyright 2026 Ittirit Saengow (อิทธิฤทธิ์ แซ่โง้ว) — RCT Labs  
Made with ❤️ from Bangkok, Thailand 🇹🇭
