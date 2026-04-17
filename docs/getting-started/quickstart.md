# Quick Start

Three examples covering the three core pillars of RCT Platform: **FDIA scoring**, **SignedAI consensus**, and **Delta Engine memory**.

---

## 1. FDIA Score — Evaluate an AI Action

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
print(f"FDIA score: {score:.4f}")
# → FDIA score: 0.8245  (deterministic float in [0.0, 1.0])
```

!!! note "Constitutional Gate"
    When `governance_penalty=1.0`, the score collapses to 0 and the action is blocked — regardless of data quality or intent.

---

## 2. SignedAI Consensus — Multi-LLM Verification

```python
from signedai.core.registry import SignedAIRegistry, RiskLevel

registry = SignedAIRegistry()

# Route a decision to the appropriate tier based on risk level
tier = registry.get_tier_for_risk(RiskLevel.HIGH)
print(f"Routing to: {tier.name}")         # → SignedAITier.S8

# Get all models in a tier
models = registry.get_models_for_tier(tier)
for m in models:
    print(f"  {m.model_id}: {m.provider}")
```

---

## 3. Delta Engine — Compressed Agent Memory

```python
from core.delta_engine.memory_delta import (
    MemoryDeltaEngine, AgentMemoryState, NPCIntentType
)

engine = MemoryDeltaEngine()

# Register an agent with initial state
engine.register_agent("agent-1", AgentMemoryState(
    agent_id="agent-1", tick=0,
    intent_type=NPCIntentType.ACCUMULATE,
    resources={"gold": 100.0},
))

# Record what changed at tick 5 (delta, not full state)
engine.record_delta(
    agent_id="agent-1", tick=5,
    intent_type=NPCIntentType.ACCUMULATE,
    action_type="trade", outcome="success",
    resource_changes={"gold": 10.0},
)

state = engine.get_state_at_tick("agent-1", tick=5)
print(f"Gold at tick 5: {state.resources['gold']}")    # → 110.0
print(f"Compression: {engine.compute_compression_ratio():.1%}")  # → ~74%
```

---

## 4. Intent Loop — JITNA Packet

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
print(packet.model_dump_json(indent=2))
```

---

## 5. Control Plane DSL

```python
from rct_control_plane import DSLParser

dsl_text = """
intent: "Deploy microservice"
steps:
  - build: docker
  - test: pytest --cov-fail-under=70
  - deploy: k8s apply
constraints:
  - no_downtime: true
"""

parser = DSLParser()
graph = parser.parse(dsl_text)
print(f"Nodes: {len(graph.nodes)}, Edges: {len(graph.edges)}")
```

---

## Next Steps

- [Core Concepts — FDIA](../concepts/fdia.md) — deep dive into the scoring engine
- [Architecture Overview](../concepts/architecture.md) — 11-layer system diagram
- [API Reference](../api/control-plane.md) — full REST API documentation
