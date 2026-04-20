# Use Case: Supply Chain — Bottleneck Detection & Recovery

Supply chains are multi-agent systems with competing intents: manufacturers ACCUMULATE raw materials, logistics nodes BELONG to delivery networks, and warehouses PROTECT stock levels. RCT models this natively.

---

## The Core Problem

Traditional supply chain software uses rule-based alerts ("stock < threshold → reorder"). This fails during multi-source disruptions because rules don't capture intent propagation — a port closure doesn't just affect one node, it cascades through every dependent node's decision.

RCT's FDIA engine enables **intent-propagation modelling**:
- A port closure → logistics node's `world_resources["capacity"]` drops
- Low resource triggers `PROTECT` intents to activate `defend` actions
- FDIA scores for `trade` actions drop across downstream nodes
- System automatically detects the bottleneck cascade before it reaches retail

---

## Quick Start

```python
from core.fdia.fdia import FDIAScorer, FDIAWeights, NPCAction, NPCIntentType
from core.delta_engine.memory_delta import MemoryDeltaEngine

scorer = FDIAScorer(weights=FDIAWeights())
engine = MemoryDeltaEngine()

# Supply chain tiers
NODES = [
    {"id": "supplier_A",   "intent": NPCIntentType.ACCUMULATE, "tier": "raw_materials"},
    {"id": "port_B",       "intent": NPCIntentType.BELONG,     "tier": "logistics"},
    {"id": "warehouse_C",  "intent": NPCIntentType.PROTECT,    "tier": "storage"},
    {"id": "distributor_D","intent": NPCIntentType.ACCUMULATE, "tier": "distribution"},
    {"id": "retail_E",     "intent": NPCIntentType.BELONG,     "tier": "retail"},
]

# Normal world state
world_normal = {"capacity": 500.0, "inventory": 800.0, "demand": 400.0}

# Disrupted world state (port closure)
world_disrupted = {"capacity": 50.0, "inventory": 800.0, "demand": 400.0}

actions = [
    NPCAction("ship_full",    "trade",     amount=100.0, resource_id="capacity"),
    NPCAction("hold_stock",   "idle",      amount=0.0),
    NPCAction("partial_ship", "trade",     amount=30.0,  resource_id="capacity"),
    NPCAction("reroute",      "explore",   amount=0.0),
    NPCAction("cooperate",    "cooperate", amount=50.0,  resource_id="inventory"),
]

# Register nodes
for node in NODES:
    engine.register_agent(node["id"], node["intent"], {"inventory": 100.0})

print("Normal world:")
for node in NODES:
    ranked = scorer.rank_actions(
        agent_intent=node["intent"],
        actions=actions,
        world_resources=world_normal,
        agent_reputation=0.90,
    )
    print(f"  {node['id']:15s} [{node['intent'].value:10s}] → {ranked[0][0].action_id}")

print("\nDisrupted world (port closure):")
for node in NODES:
    ranked = scorer.rank_actions(
        agent_intent=node["intent"],
        actions=actions,
        world_resources=world_disrupted,
        agent_reputation=0.90,
    )
    print(f"  {node['id']:15s} [{node['intent'].value:10s}] → {ranked[0][0].action_id}")
```

**Expected pattern:**
- Normal: `supplier` and `distributor` → `ship_full`, `port` → `ship_full`, `warehouse` → `cooperate`
- Disrupted: `port` → `reroute`, `warehouse` → `hold_stock`, `distributor` → `partial_ship`

The FDIA engine automatically shifts decisions when resource levels change — no rule rewriting needed.

---

## Bottleneck Detection

```python
def detect_bottleneck(
    nodes: list,
    world: dict,
    scorer: FDIAScorer,
) -> list:
    """
    Return list of nodes where the best action shifted to defensive/idle.
    These are the bottleneck nodes.
    """
    bottlenecks = []
    defensive = {"idle", "hold_stock"}

    for node in nodes:
        ranked = scorer.rank_actions(
            agent_intent=node["intent"],
            actions=actions,
            world_resources=world,
            agent_reputation=0.90,
        )
        if ranked[0][0].action_id in defensive:
            bottlenecks.append(node["id"])

    return bottlenecks

bottlenecks = detect_bottleneck(NODES, world_disrupted, scorer)
print(f"Bottleneck nodes: {bottlenecks}")
# → ["port_B", "warehouse_C"]
```

---

## Multi-Tier Cascade Simulation

Run the full simulation with [`examples/simulation_demo.py`](../../examples/simulation_demo.py):

```bash
python examples/simulation_demo.py --ticks 20 --agents 5 --verbose
```

The EPSILON agent uses `DISCOVER` intent and will `explore` (reroute) when capacity drops, while DELTA (`DOMINATE`) will attempt to capture remaining capacity.

---

## Memory Replay for Post-Incident Analysis

After a disruption, replay any node's state at any tick:

```python
# What was warehouse_C doing at tick 8?
state = engine.get_state_at_tick("warehouse_C", tick=8)
print(f"Tick 8 state: {state.action_history}")
print(f"Resources at tick 8: {state.resources}")
```

This enables post-incident root cause analysis without storing full snapshots.

---

## Governance: Emergency Rerouting Policy

```python
from rct_control_plane.policy_language import (
    PolicyEvaluator, PolicyRule, PolicyCondition,
    PolicyAction, PolicyPriority, PolicyScope, ConditionOperator,
)

# Auto-approve emergency rerouting when capacity < 20%
evaluator.register_policy(PolicyRule(
    name="Emergency Reroute Approval",
    description="Auto-approve rerouting actions during capacity crisis",
    scope=PolicyScope.INTENT,
    priority=PolicyPriority.HIGH,
    conditions=[
        PolicyCondition(
            field="goal",
            operator=ConditionOperator.CONTAINS,
            value="reroute",
        )
    ],
    action=PolicyAction.APPROVE,
    action_metadata={"reason": "Emergency capacity response — auto-approved"},
))
```

---

## See Also

- [FDIA Engine](../concepts/fdia-engine.md)
- [Game AI Use Case](game-ai.md) — multi-agent tick simulation patterns
- [`examples/simulation_demo.py`](../../examples/simulation_demo.py)
- [Governance Layer](../concepts/governance.md)
