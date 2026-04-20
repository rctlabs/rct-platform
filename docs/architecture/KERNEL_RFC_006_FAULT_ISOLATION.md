# RFC-006: Fault Isolation & Recovery Domains

**Status:** Draft  
**Authors:** RCT Kernel Team  
**Created:** 2026-02-26  
**Layer:** OS Primitive (Reliability)  
**Implements:** `core/kernel/fault_isolation.py` (Plan 30)  
**Test Evidence:** `tests/kernel/test_fault_isolation.py` (26 tests)  
**Depends on:** RFC-002 (ProcessTable — state transitions for recovery)

---

## Abstract

This RFC formalizes the Fault Isolation Manager — the kernel component that
ensures a single agent crash never kills the simulation tick. It classifies
exceptions into three severity levels (RECOVERABLE, QUARANTINE, EXILE), applies
automatic recovery policies, and maintains structured fault logs.

The core invariant: **process isolation guarantees that any individual agent
failure is contained and does not propagate to other agents or the kernel.**

## Motivation

In a multi-agent simulation, exceptions are inevitable:
- Division by zero in FDIA scoring
- Key lookup failures on shared resources
- Timeout in LLM integration calls
- Stack overflow from recursive agent strategies

Without fault isolation, any exception crashes the entire simulation tick,
affecting all agents. The Fault Isolation Manager provides per-agent containment
with graduated recovery policies.

## Specification

### 1. FaultSeverity Classification

Three severity levels with distinct recovery policies:

| Severity       | Recovery Policy                        | Agent State After  |
|----------------|----------------------------------------|--------------------|
| `RECOVERABLE`  | Skip action this tick, resume next tick | READY (unchanged)  |
| `QUARANTINE`   | Block agent for N ticks (default: 3)   | BLOCKED (timed)    |
| `EXILE`        | Immediately terminate agent            | TERMINATED         |

### 2. Exception-to-Severity Mapping

Default classification by Python exception type:

| Severity       | Exception Types                                    |
|----------------|----------------------------------------------------|
| `RECOVERABLE`  | ValueError, KeyError, IndexError, TypeError, AttributeError, ArithmeticError |
| `QUARANTINE`   | RuntimeError, TimeoutError, OSError                |
| `EXILE`        | RecursionError, MemoryError, SystemError           |

#### Classification Algorithm

1. **Exact type match** — check `type(exception)` against fault map
2. **Inheritance check** — check `isinstance()` in severity order (EXILE first, then QUARANTINE, then RECOVERABLE)
3. **Fallback** — unknown exception types default to `QUARANTINE`

Classification is deterministic and does not depend on exception message content.

### 3. Recovery Policies

#### RECOVERABLE

```
if agent.state == RUNNING:
    process_table.set_ready(pid)    # RUNNING → READY
# Agent remains READY, will be scheduled next tick
# Action for THIS tick is skipped (no side effects)
```

**Rationale:** Transient errors (key not found, bad value) are likely to
resolve next tick when world state changes.

#### QUARANTINE

```
until_tick = current_tick + quarantine_ticks  # default: 3
if agent.state == RUNNING:
    process_table.block(pid, until_tick=until_tick)
elif agent.state == READY:
    process_table.transition_state(pid, RUNNING)
    process_table.block(pid, until_tick=until_tick)
```

**Rationale:** Non-transient errors (runtime failures, timeouts) need cooling
period. Agent is blocked for `quarantine_ticks` before re-entering the ready
queue. Auto-unblocked by `ProcessTable.unblock_expired()` during scheduler
`build_schedule()` (RFC-003).

#### EXILE

```
process_table.terminate(pid, tick, reason="severe_fault")
```

**Rationale:** Catastrophic errors (stack overflow, memory exhaustion) indicate
an agent that cannot safely continue. Immediate termination prevents cascading
failures.

### 4. FaultRecord (Structured Fault Log)

```python
@dataclass
class FaultRecord:
    pid: int                   # Faulted agent's PID
    agent_id: str              # Application-level agent name
    tick: int                  # Tick at which fault occurred
    phase: str                 # Simulation phase (OBSERVE, DECIDE, ACT)
    exception_type: str        # e.g. "ValueError", "RuntimeError"
    message: str               # First 200 chars of exception message
    traceback_hash: str        # MD5 hash of traceback (12-char hex)
    severity: FaultSeverity    # Classified severity
    recovery_action: str       # What recovery was applied
```

**Traceback hashing** enables grouping duplicate faults across agents and ticks
without storing full tracebacks (privacy + space efficiency).

### 5. FaultIsolationManager API

```python
class FaultIsolationManager:
    def __init__(
        self,
        process_table: ProcessTable,       # For state transitions
        quarantine_ticks: int = 3,         # QUARANTINE duration
        fault_map: Dict[Type, FaultSeverity]  # Custom mapping (optional)
    )
```

| Method                    | Description                                |
|---------------------------|--------------------------------------------|
| `on_agent_fault(pid, agent_id, tick, phase, exception)` | Classify + recover + log |
| `get_fault_log(pid=None)` | Structured fault records (filterable by PID) |
| `get_fault_count(pid)`    | Total faults for one agent                 |
| `get_total_faults()`      | Total faults across all agents             |
| `get_fault_summary()`     | Count by severity (RECOVERABLE/QUARANTINE/EXILE) |
| `get_healthy_ratio()`     | Fraction of alive agents with zero faults  |

### 6. Integration with SimulationEngine

```python
# Inside SimulationEngine._run_tick():
for pid in execution_order:
    try:
        # ... agent OBSERVE → DECIDE → ACT ...
        pass
    except Exception as e:
        fault_manager.on_agent_fault(pid, agent_id, tick, phase, e)
        # Simulation continues with next agent
        # No tick-level crash
```

### 7. Health Metrics

`get_healthy_ratio()` computes:

```
healthy_ratio = count(alive agents with 0 faults) / count(all alive agents)
```

This metric is included in SimulationResult for post-run analysis:
- 1.0 = all alive agents are fault-free
- < 0.5 = majority of agents have experienced faults (potential systemic issue)

### 8. Custom Fault Maps

The default fault map can be overridden for domain-specific exception handling:

```python
custom_map = {
    MyDomainError: FaultSeverity.RECOVERABLE,
    ExternalAPIError: FaultSeverity.QUARANTINE,
    CriticalStateCorruption: FaultSeverity.EXILE,
}
manager = FaultIsolationManager(process_table, fault_map=custom_map)
```

Custom maps are merged with defaults — explicit entries override defaults for
the same exception type.

## Test Coverage

26 tests in `tests/kernel/test_fault_isolation.py` covering:

- Classification of all default exception types
- RECOVERABLE recovery (agent stays READY)
- QUARANTINE recovery (agent BLOCKED for N ticks)
- EXILE recovery (agent TERMINATED)
- Fault record structure and serialization
- Traceback hash determinism (same exception → same hash)
- Fault count per agent tracking
- Total fault summary by severity
- Healthy ratio calculation (0 faults, some faults, all faulted)
- Custom fault map override
- Unknown exception defaults to QUARANTINE
- Multiple faults for same agent (escalation tracking)

## Interaction with Other RFCs

| RFC   | Relationship                                                    |
|-------|-----------------------------------------------------------------|
| RFC-002 | Uses ProcessTable for state transitions (READY/BLOCKED/TERMINATED) |
| RFC-003 | Blocked agents excluded from next scheduler pass; unblocked by scheduler |
| RFC-004 | Exiled agents' mailboxes should be deregistered (future integration) |
| RFC-005 | Fault Isolation may revoke capabilities for faulted agents (future) |

## Backward Compatibility

- **Full backward compatibility.** FaultIsolationManager wraps existing
  try/except patterns — no changes to exception handling semantics.
- Simulations that do not use FaultIsolationManager continue to propagate
  exceptions normally (existing behavior preserved).

## Core Invariant

**A single agent crash NEVER kills the simulation tick.**

This is the defining property of the Fault Isolation layer. It is validated
by test cases that inject exceptions of every severity level and verify that:
1. The faulted agent is correctly recovered/quarantined/exiled
2. All other agents in the same tick execute normally
3. SimulationEngine completes the tick without raising
