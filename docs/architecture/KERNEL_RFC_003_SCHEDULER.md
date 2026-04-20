# RFC-003: Tick Scheduler & Priority Execution

**Status:** Draft  
**Authors:** RCT Kernel Team  
**Created:** 2026-02-26  
**Layer:** OS Primitive (Scheduling)  
**Implements:** `core/kernel/scheduler.py` (Plan 27)  
**Test Evidence:** `tests/kernel/test_scheduler.py` (30 tests)  
**Depends on:** RFC-002 (Process Model — ProcessTable, AgentDescriptor)

---

## Abstract

This RFC formalizes the Tick Scheduler — the kernel component responsible for
determining per-tick agent execution order. It replaces the naive
`for agent in sorted(agents)` loop with a policy-driven dispatch that respects
priority, prevents starvation, and tracks scheduling metrics.

Three scheduling policies are specified: ROUND_ROBIN, WEIGHTED_PRIORITY, and
INTENT_WEIGHTED.

## Motivation

Without a formal scheduler, all agents execute in arbitrary order every tick.
This creates problems:

- **Priority inversion** — high-priority agents (DOMINATE intent) may execute
  after low-priority agents (NEUTRAL)
- **Starvation** — agents with low priority may never execute if high-priority
  agents dominate the queue
- **Non-determinism** — `dict` iteration order in Python is insertion-order,
  but simulation configuration order varies

The Tick Scheduler solves all three problems with configurable policies and
built-in starvation prevention.

## Specification

### 1. SchedulingPolicy Enum

```python
class SchedulingPolicy(str, Enum):
    ROUND_ROBIN = "ROUND_ROBIN"           # Deterministic PID-order
    WEIGHTED_PRIORITY = "WEIGHTED_PRIORITY" # Priority + starvation boost
    INTENT_WEIGHTED = "INTENT_WEIGHTED"     # Intent × priority × starvation
```

### 2. SchedulerConfig

```python
@dataclass
class SchedulerConfig:
    policy: SchedulingPolicy = ROUND_ROBIN
    max_starvation_ticks: int = 5       # Boost after N ticks without execution
    starvation_boost: float = 2.0       # Priority increase for starved agents
    intent_weights: Dict[NPCIntentType, float]  # Per-intent multipliers
```

Default `intent_weights` mirror `INTENT_PRIORITY` from RFC-002:

| Intent      | Weight |
|-------------|--------|
| DOMINATE    | 3.0    |
| ACCUMULATE  | 2.5    |
| DISCOVER    | 2.0    |
| BELONG      | 1.8    |
| PROTECT     | 1.5    |
| NEUTRAL     | 1.0    |

### 3. Scheduling Algorithms

#### ROUND_ROBIN

```
execution_order = sorted(ready_agents, key=lambda d: d.pid)
```

- **Deterministic:** Same PID set → same order always.
- **Fair:** Every ready agent executes every tick.
- **No priority awareness:** Ignores agent priority entirely.

#### WEIGHTED_PRIORITY

```
effective_priority(agent) = agent.priority + starvation_boost(agent)
execution_order = sorted(ready_agents, key=effective_priority, descending)
```

- Deterministic tie-breaking by PID (ascending).
- Starvation boost kicks in after `max_starvation_ticks` without execution.

#### INTENT_WEIGHTED

```
effective_priority(agent) = agent.priority × intent_weight[agent.intent] + starvation_boost
execution_order = sorted(ready_agents, key=effective_priority, descending)
```

- Combines base priority with intent-specific weights.
- Same starvation prevention mechanism as WEIGHTED_PRIORITY.

### 4. Starvation Prevention

For any agent that has not executed in `max_starvation_ticks` consecutive ticks:

```
starvation_boost(pid) = {
    config.starvation_boost  if (current_tick - last_executed[pid]) >= max_starvation_ticks
    0.0                      otherwise
}
```

This ensures no agent is perpetually starved, regardless of priority.

**Metric tracking:** `SchedulerMetrics.starvation_boosts` counts how many times
the boost was applied across all ticks.

### 5. AgentPriorityQueue

Min-heap implementation (negated for max-priority-first behavior):

| Operation           | Complexity | Description                        |
|---------------------|------------|------------------------------------|
| `push(pid, prio)`   | O(log n)   | Insert agent with priority         |
| `pop()`             | O(log n)   | Remove highest-priority agent      |
| `peek()`            | O(1)       | View highest-priority without removal |
| `update_priority()`| O(n)       | Rebuild entry (acceptable for <10k agents) |
| `to_sorted_list()` | O(n log n) | All entries sorted by priority desc |

Tie-breaking: when two agents have equal effective priority, the agent with
the **lower PID** executes first (deterministic).

### 6. TickScheduler Usage Contract

```python
scheduler = TickScheduler(process_table, config)

for tick in range(num_ticks):
    # 1. Build execution order (auto-unblocks expired agents)
    execution_order = scheduler.build_schedule(tick)
    
    # 2. Execute agents in order
    for pid in execution_order:
        # ... run agent ...
        pass
    
    # 3. Record execution (for starvation tracking)
    scheduler.record_execution(execution_order, tick)
```

**Build schedule** automatically calls `process_table.unblock_expired(tick)`
before collecting ready agents.

### 7. SchedulerMetrics

```python
@dataclass
class SchedulerMetrics:
    total_schedules_built: int = 0    # Number of ticks scheduled
    total_agents_scheduled: int = 0   # Cumulative agents dispatched
    starvation_boosts: int = 0        # Starvation prevention activations
    skipped_agents: int = 0           # BLOCKED/TERMINATED agents skipped
```

## Test Coverage

30 tests in `tests/kernel/test_scheduler.py` covering:

- ROUND_ROBIN deterministic order validation
- WEIGHTED_PRIORITY ordering by effective priority
- INTENT_WEIGHTED ordering with intent multipliers
- Starvation prevention after N ticks
- AgentPriorityQueue push/pop/peek/update operations
- Deterministic tie-breaking by PID
- Empty ready set → empty schedule
- Metrics accumulation across ticks
- Auto-unblock integration with ProcessTable

## Interaction with Other RFCs

| RFC   | Relationship                                                    |
|-------|-----------------------------------------------------------------|
| RFC-002 | Reads ProcessTable state; uses AgentDescriptor.priority and intent |
| RFC-004 | Scheduler determines execution order; IPC delivers messages between ticks |
| RFC-005 | Syscall layer may modify priority via SYS_GET_STATE             |
| RFC-006 | Fault Isolation may block agents, affecting next scheduler pass |

## Backward Compatibility

- **Full backward compatibility.** SimulationEngine can use TickScheduler
  as a drop-in replacement for manual agent ordering.
- Default ROUND_ROBIN policy produces identical results to the previous
  `sorted(agents)` approach.
