# RFC-005: Syscall Interface & Capability Model

**Status:** Draft  
**Authors:** RCT Kernel Team  
**Created:** 2026-02-26  
**Layer:** OS Primitive (API Boundary)  
**Implements:** `core/kernel/syscall.py` (Plan 29)  
**Test Evidence:** `tests/kernel/test_syscall.py` (34 tests)  
**Depends on:** RFC-002 (ProcessTable), RFC-003 (Scheduler), RFC-004 (IPC/MessageBus)

---

## Abstract

This RFC formalizes the Kernel Syscall Interface — the single API boundary
through which all agent-to-kernel interactions must flow. Every operation that
modifies kernel state (resource allocation, agent spawn, memory commit, message
send) goes through capability-checked, quota-validated, audit-logged syscalls.

Direct WorldState mutation is **no longer permitted by convention.** All state
changes are mediated by the syscall layer.

## Motivation

Without a formal syscall boundary:

- **No access control** — any agent can modify any resource without permission
- **No quota enforcement** — agents can allocate unlimited resources
- **No audit trail** — state changes are invisible to governance
- **No latency tracking** — impossible to profile kernel operations

The Syscall Interface solves all four problems by interposing a capability-checked
gateway between agents and kernel state.

## Specification

### 1. SyscallCode Enumeration

10 syscall codes covering all kernel operations:

| Code              | Description                          | Modifies State? |
|-------------------|--------------------------------------|-----------------|
| `SYS_ALLOC`       | Reserve resources from world pool    | Yes             |
| `SYS_RELEASE`     | Release resources back to pool       | Yes             |
| `SYS_SPAWN`       | Spawn a new agent process            | Yes             |
| `SYS_TERMINATE`   | Terminate an agent process           | Yes             |
| `SYS_COMMIT_DELTA`| Commit memory delta                  | Yes             |
| `SYS_ROLLBACK`    | Rollback memory state                | Yes             |
| `SYS_QUERY`       | Query resource availability          | No (read-only)  |
| `SYS_SEND_MSG`    | Send IPC message                     | Yes             |
| `SYS_CHECKPOINT`  | Force memory checkpoint              | No              |
| `SYS_GET_STATE`   | Read own agent state                 | No (read-only)  |

### 2. KernelCapability Token

Per-agent permission token controlling syscall access:

```python
@dataclass
class KernelCapability:
    pid: int                              # Owner PID
    allowed_syscalls: Set[SyscallCode]    # Permitted syscall codes
    resource_quotas: Dict[str, float]     # {resource_id: max_amount}
    expires_at_tick: Optional[int]        # None = never expires
```

#### Capability Checks

1. **Existence** — PID must have a registered capability token
2. **Expiry** — Token must not be expired (tick > expires_at_tick)
3. **Syscall permission** — Requested syscall code must be in `allowed_syscalls`
4. **Quota** — Requested resource amount must be within `resource_quotas`

If any check fails, the syscall returns `SyscallResult(success=False)` with
a diagnostic `error` string.

### 3. CapabilityRegistry

Central registry managing all agent capabilities:

| Operation                  | Description                              |
|---------------------------|------------------------------------------|
| `grant(pid, syscalls, quotas, expires)` | Grant capabilities (replaces existing) |
| `grant_default(pid, resources)` | Full access with default quotas (200.0 per resource) |
| `revoke(pid)`              | Revoke all capabilities for PID          |
| `check(pid, code, tick)`   | Validate capability for syscall at tick  |
| `revoke_expired(tick)`     | Bulk revoke expired tokens               |

#### Default Grant

`grant_default()` provides full access to all 10 syscall codes with a
per-resource quota of 200.0 units. This is the standard grant for newly
spawned agents.

### 4. SyscallResult

Standardized return type for every kernel syscall:

```python
@dataclass
class SyscallResult:
    success: bool                    # Whether syscall succeeded
    syscall_code: SyscallCode        # Which syscall was called
    pid: int                         # Caller's PID
    tick: int                        # Tick at call time
    payload: Dict[str, Any]          # Syscall-specific return data
    error: Optional[str]             # Error message (None if success)
    latency_us: int                  # Execution time in microseconds
```

Every syscall updates `latency_us` using `time.perf_counter_ns()` for
sub-microsecond precision.

### 5. KernelSyscallInterface

The unified gateway class. Constructor dependencies:

```python
KernelSyscallInterface(
    world: WorldState,                  # Resource pools
    process_table: ProcessTable,        # Agent registry (RFC-002)
    memory_engine: MemoryDeltaEngine,   # Memory delta layer
    message_bus: KernelMessageBus,      # IPC layer (RFC-004, optional)
    capability_registry: CapabilityRegistry  # Permission management
)
```

#### Syscall Execution Pipeline

Every syscall follows the same pipeline:

```
Agent → sys_*(pid, ..., tick)
  ├── 1. Capability check (allowed_syscalls, expiry)
  ├── 2. Quota check (resource_quotas)
  ├── 3. Execute operation
  ├── 4. Record latency
  └── 5. Append to audit log → SyscallResult
```

#### Syscall Implementations

| Syscall             | Parameters                           | Returns in Payload          |
|---------------------|--------------------------------------|-----------------------------|
| `sys_alloc`         | pid, resource_id, amount, tick       | resource_id, amount, reserved |
| `sys_release`       | pid, resource_id, amount, tick       | resource_id, amount         |
| `sys_query`         | pid, resource_id, tick               | available, capacity, utilization |
| `sys_spawn`         | pid, child_agent_id, intent, role, tick | child_pid, child_agent_id |
| `sys_terminate`     | pid, target_pid, tick                | target_pid                  |
| `sys_commit_delta`  | pid, agent_id, tick, **delta_kwargs  | agent_id                    |
| `sys_rollback`      | pid, to_tick, tick                   | rolled_back_to              |
| `sys_send_msg`      | pid, receiver_pid, intent, payload, tick | receiver_pid, status     |
| `sys_checkpoint`    | pid, tick                            | total_deltas                |
| `sys_get_state`     | pid, tick                            | AgentDescriptor.to_dict()   |

### 6. Audit Log & Metrics

All syscall results are appended to `_audit_log: List[SyscallResult]`.

```python
def get_audit_log(pid: Optional[int] = None) -> List[Dict]
def get_syscall_metrics() -> Dict[str, Any]
```

Metrics tracked:

| Metric            | Description                          |
|-------------------|--------------------------------------|
| `total_calls`     | Total syscalls executed              |
| `denied_calls`    | Capability/quota denials             |
| `by_code`         | Per-syscall-code execution counts    |
| `denied_by_code`  | Per-syscall-code denial counts       |
| `avg_latency_us`  | Average syscall latency (microseconds) |

### 7. Cross-Component Integration

```
┌──────────────┐     ┌─────────────────────┐     ┌───────────────┐
│  Agent Code  │────▶│ KernelSyscallInterface │────▶│  WorldState   │
└──────────────┘     │                     │     │  ProcessTable │
                     │  1. Check Capability│     │  MemoryEngine │
                     │  2. Check Quota     │     │  MessageBus   │
                     │  3. Execute         │     └───────────────┘
                     │  4. Audit Log       │
                     └─────────────────────┘
```

## Test Coverage

34 tests in `tests/kernel/test_syscall.py` covering:

- All 10 syscall codes execution (success path)
- Capability denial for each syscall code
- Quota exceeded rejection (SYS_ALLOC)
- Expired capability token handling
- SYS_SPAWN creates child with correct parent PID
- SYS_TERMINATE cleans up mailbox (IPC integration)
- SYS_SEND_MSG delivers through MessageBus
- Audit log recording for every syscall
- Latency measurement (non-zero latency_us)
- Metrics accumulation (total_calls, denied_calls, by_code)
- CapabilityRegistry grant/revoke/check operations
- Bulk expired capability revocation

## Interaction with Other RFCs

| RFC   | Relationship                                                    |
|-------|-----------------------------------------------------------------|
| RFC-002 | SYS_SPAWN/SYS_TERMINATE modify ProcessTable                   |
| RFC-003 | SYS_GET_STATE reads scheduler-relevant agent state             |
| RFC-004 | SYS_SEND_MSG wraps KernelMessageBus.send() with capability check |
| RFC-006 | Fault Isolation may revoke capabilities for faulted agents      |
| RFC-001 | JITNA negotiation uses SYS_SEND_MSG for message transport      |

## Backward Compatibility

- **Full backward compatibility.** The syscall interface is an additive layer.
  Existing code that directly accesses WorldState will continue to work, but
  new code SHOULD use syscalls for audit and access control.
- No existing function signatures are changed.
