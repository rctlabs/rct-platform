# Use Case: Game AI & NPC Behavior Systems

The RCT Platform's FDIA engine was designed with multi-agent simulation as a first-class use case. Every NPC in a game world can have a persistent intent, make constitutionally-consistent decisions, and have its behavior replayed exactly for debugging.

---

## Why RCT for Game AI?

Traditional game AI uses behaviour trees or finite state machines — rule-based systems that become unmaintainable at scale. RCT replaces hand-coded rules with a **scoring function** driven by agent intent, world resources, and social context.

| Traditional AI | RCT FDIA |
|---|---|
| Hand-coded transitions | Intent-driven scoring |
| Bugs from state explosion | Pure function — no hidden state |
| Non-reproducible behavior | Deterministic — 100% replay |
| No memory compression | Delta engine — 74% less RAM |
| No governance hook | Constitutional rules per NPC tier |

---

## Scenario: Trade Economy

**30 agents, 200 ticks, dominant intent: ACCUMULATE**

Agents compete over food, ore, and energy pools. ACCUMULATE-intent agents will preferentially trade and hoard. PROTECT-intent agents will defend existing stocks. DOMINATE-intent agents will attack when resources are scarce.

```python
from core.fdia.fdia import FDIAScorer, FDIAWeights, NPCAction, NPCIntentType
from core.delta_engine.memory_delta import MemoryDeltaEngine

scorer = FDIAScorer(weights=FDIAWeights())
engine = MemoryDeltaEngine()

# Create 30 agents — 50% ACCUMULATE, 30% PROTECT, 20% NEUTRAL
agents = [
    {"id": f"trader_{i}", "intent": NPCIntentType.ACCUMULATE, "resources": {"gold": 100.0}}
    for i in range(15)
] + [
    {"id": f"guard_{i}", "intent": NPCIntentType.PROTECT, "resources": {"gold": 80.0}}
    for i in range(9)
] + [
    {"id": f"wanderer_{i}", "intent": NPCIntentType.NEUTRAL, "resources": {"gold": 60.0}}
    for i in range(6)
]

# Register all agents
for a in agents:
    engine.register_agent(a["id"], a["intent"], a["resources"])

# Run one tick
world = {"gold": 2000.0, "ore": 1500.0, "food": 1200.0}
for a in agents:
    candidates = [
        NPCAction("trade",     "trade",     amount=20.0, resource_id="gold"),
        NPCAction("attack",    "attack",    amount=10.0, resource_id="gold"),
        NPCAction("cooperate", "cooperate", amount=15.0, resource_id="gold"),
        NPCAction("idle",      "idle"),
    ]
    ranked = scorer.rank_actions(
        agent_intent=a["intent"],
        actions=candidates,
        world_resources=world,
        agent_reputation=0.85,
    )
    best_action, score = ranked[0]
    print(f"{a['id']:15s} [{a['intent'].value:10s}] → {best_action.action_id} ({score:.4f})")
```

**Expected output pattern:**
- `trader_*`: `trade` wins (ACCUMULATE + trade = high alignment)
- `guard_*`: `cooperate` or `idle` wins (PROTECT + attack = low score)
- `wanderer_*`: mixed (NEUTRAL has no strong bias)

---

## Scenario: Civil Conflict

**45 agents, 600 ticks, 40% DOMINATE intent**

When resources drop below a threshold, DOMINATE agents switch to `attack`. This creates a revenge spiral: attacked agents lower their `agent_reputation` of the attacker, which feeds back into lower FDIA scores for future cooperation between those agents.

```python
# Governance hook: flag agents with > 3 attacks in last 10 ticks
def check_aggression(agent_id: str, engine: MemoryDeltaEngine) -> bool:
    recent = engine.get_recent_actions(agent_id, n=10)
    return recent.count("attack") > 3

# If flagged, apply governance_penalty in next tick
governance_penalty = 0.30 if check_aggression("aggressor_01", engine) else 0.0
```

---

## Running the Demo

Run a simulation:

```bash
python -m rct.simulation.run --ticks 15 --agents 6 --verbose
```

---

## Memory at Scale

For a 30-agent, 200-tick scenario:
- Full state storage: 30 agents × 200 ticks × ~2 KB = **12 MB**
- Delta engine: baseline per agent + deltas ≈ **3.1 MB** (~74% compression)

The `MemoryDeltaEngine` keeps a baseline snapshot at `checkpoint_interval` ticks and stores only `MemoryDelta` records between checkpoints.

---

## See Also

- [FDIA Engine](../concepts/fdia.md)
- [RCT-7 Thinking Protocol](../concepts/rct-7-thinking.md)
