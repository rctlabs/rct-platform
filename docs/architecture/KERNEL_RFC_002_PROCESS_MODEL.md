# RFC-002: Agent Process Model

**Status:** Draft  
**Authors:** RCT Kernel Team  
**Created:** 2026-02-26  
**Layer:** OS Primitive (Foundation)  
**Implements:** `core/kernel/process_model.py` (Plan 26)  
**Test Evidence:** `tests/kernel/test_process_model.py` (45 tests)

---

## Abstract

This RFC formalizes the Agent Process Model — the foundational OS-level
abstraction that transforms NPC agents from plain dataclasses into managed
processes within the RCT Cognitive Kernel. It defines the lifecycle state
machine, per-agent metadata structure (AgentDescriptor), the kernel-level
process registry (ProcessTable), and the factory layer (AgentLifecycleManager).

All higher OS primitives (Scheduler, IPC, Syscall, Fault Isolation) depend on
this specification.

## Motivation

Prior to Plan 26, NPC agents existed as flat `NPCAgent` dataclasses with no
formal lifecycle, no unique process identifier, and no kernel-level tracking.
This made scheduling, isolation, and audit impossible. The Process Model
introduces:

- **PID-based identity** — every agent gets a unique process identifier
- **Lifecycle state machine** — formal states with validated transitions
- **Priority management** — intent-aware priority for scheduling
- **Resource quota tracking** — per-agent resource caps enforced by Syscall layer
- **Deterministic snapshots** — SHA256-hashable canonical state for audit

## Specification

### 1. AgentProcessState (Lifecycle State Machine)

Five lifecycle states with strictly validated transitions:

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ CREATED │────▶│  READY  │────▶│ RUNNING │
└─────────┘     └────┬────┘     └──┬──┬───┘
                     │             │  │
                     │     ┌───────┘  │
                     │     ▼          │
                     │  ┌─────────┐   │
                     │  │ BLOCKED │   │
                     │  └────┬────┘   │
                     ▼       ▼        ▼
                ┌──────────────────────────┐
                │       TERMINATED         │
                └──────────────────────────┘
```

#### Legal Transitions

| From        | To                              | Trigger                          |
|-------------|---------------------------------|----------------------------------|
| CREATED     | READY                           | ProcessTable.activate()          |
| READY       | RUNNING                         | Scheduler dispatches agent       |
| READY       | TERMINATED                      | Governance exile                 |
| RUNNING     | READY                           | Agent yields / tick ends         |
| RUNNING     | BLOCKED                         | I/O wait / quarantine            |
| RUNNING     | TERMINATED                      | Normal exit / severe fault       |
| BLOCKED     | READY                           | Block timer expires              |
| BLOCKED     | TERMINATED                      | Severe fault during block        |
| TERMINATED  | *(none — terminal state)*       | —                                |

#### Invariants

- `TERMINATED` is a **terminal state** — no further transitions are legal.
- `CREATED → READY` is the **only** exit from `CREATED`.
- Any illegal transition raises `InvalidStateTransition(pid, current, target)`.
- All transitions are **synchronous** and **deterministic** (no async, no randomness).

### 2. AgentDescriptor (Per-Agent Metadata)

```python
@dataclass
class AgentDescriptor:
    pid: int                          # Unique process ID (assigned by ProcessTable)
    agent_id: str                     # Application-level name ("agent_0001")
    parent_pid: int = 0               # Spawner's PID (0 = kernel-spawned)
    state: AgentProcessState          # Current lifecycle state
    priority: float = 1.0             # Scheduling priority [0.1 .. 10.0]
    intent: NPCIntentType             # Primary intent (DOMINATE, ACCUMULATE, ...)
    role: str = "ANALYST"             # Governance role
    resource_quota: Dict[str, float]  # {resource_id: max_amount}
    birth_tick: int = 0               # Tick at which agent was spawned
    exit_tick: Optional[int] = None   # Tick at which agent terminated
    blocked_until_tick: Optional[int] # Tick when BLOCKED expires
```

#### Deterministic Serialization

`to_dict()` returns a canonical dict with:
- Sorted `resource_quota` keys
- Rounded float values (4 decimal places)
- Enum values as strings

This enables SHA256-based snapshot hashing for audit and determinism proofs.

### 3. ProcessTable (Kernel Process Registry)

The ProcessTable is an `OrderedDict`-backed registry providing:

| Operation              | Complexity | Description                               |
|------------------------|------------|-------------------------------------------|
| `spawn_agent(desc)`    | O(1)       | Register agent, assign auto-increment PID |
| `terminate(pid, tick)` | O(1)       | Set TERMINATED + exit_tick (idempotent)   |
| `transition_state()`   | O(1)       | Validate & apply state transition         |
| `activate(pid)`        | O(1)       | CREATED → READY convenience              |
| `set_running(pid)`     | O(1)       | READY → RUNNING convenience              |
| `block(pid, until)`    | O(1)       | RUNNING → BLOCKED with optional timer    |
| `unblock_expired(tick)`| O(n)       | Auto-unblock expired BLOCKED agents       |
| `get_descriptor(pid)`  | O(1)       | Lookup by PID                             |
| `list_by_state(state)` | O(n)       | Query agents in specific state            |
| `to_snapshot()`        | O(n)       | SHA256-hashable canonical dict            |
| `to_hash()`            | O(n)       | SHA256 hex digest of snapshot             |

#### PID Assignment

- PIDs are auto-incremented starting from 1.
- PID 0 is reserved for "kernel-spawned" parent reference.
- PIDs are never reused within a simulation run.

### 4. AgentLifecycleManager (Factory)

High-level factory that creates agents from simulation configuration:

- `create_from_lists()` — batch-spawn agents with intent-based priority defaults
- `spawn_child()` — create child agent from existing parent (lineage tracking)
- `terminate_agent()` — graceful termination with exit_tick recording
- `get_lineage()` — ancestry chain [pid, parent, grandparent, ...]

#### Intent-to-Priority Defaults

| Intent      | Default Priority |
|-------------|-----------------|
| DOMINATE    | 3.0             |
| ACCUMULATE  | 2.5             |
| DISCOVER    | 2.0             |
| BELONG      | 1.8             |
| PROTECT     | 1.5             |
| NEUTRAL     | 1.0             |

### 5. Error Handling

| Exception                 | Condition                          |
|---------------------------|------------------------------------|
| `InvalidStateTransition`  | Illegal state transition attempted |
| `KeyError`                | PID not found in ProcessTable      |

`InvalidStateTransition` carries `pid`, `current`, and `target` fields for
diagnostic purposes.

## Test Coverage

45 tests in `tests/kernel/test_process_model.py` covering:

- State machine completeness (all states, all transitions)
- Terminal state invariant (TERMINATED has no exits)
- AgentDescriptor defaults and serialization
- ProcessTable spawn/terminate/query operations
- PID auto-increment and uniqueness
- Block/unblock timer semantics
- AgentLifecycleManager batch creation
- Parent-child lineage tracking
- Priority clamping [0.1 .. 10.0]
- Snapshot determinism (SHA256 hash identity across runs)

## Interaction with Other RFCs

| RFC   | Relationship                                                    |
|-------|-----------------------------------------------------------------|
| RFC-003 | Scheduler reads ProcessTable to build execution order          |
| RFC-004 | IPC uses PID for message addressing                            |
| RFC-005 | Syscall uses PID for capability checks; SYS_SPAWN creates agents|
| RFC-006 | Fault Isolation uses ProcessTable to block/terminate faulted agents |

## Backward Compatibility

- **Full backward compatibility.** Existing `NPCAgent` and `SimulationEngine` code
  continues to work. ProcessTable is an additive layer — simulation can run with
  or without it.
- No breaking changes to any existing API.
