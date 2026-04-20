# RFC-004: Inter-Process Communication (IPC) Protocol

**Status:** Draft  
**Authors:** RCT Kernel Team  
**Created:** 2026-02-26  
**Layer:** OS Primitive (Communication)  
**Implements:** `core/kernel/ipc.py` (Plan 28)  
**Test Evidence:** `tests/kernel/test_ipc.py` (25 tests)  
**Depends on:** RFC-002 (Process Model — PID addressing), RFC-003 (Scheduler — tick ordering)

---

## Abstract

This RFC formalizes the kernel-level Inter-Process Communication (IPC) system
for agent-to-agent messaging within the RCT Cognitive Kernel. It specifies
typed, intent-aware messages with TTL, per-agent bounded mailboxes, centralized
routing with governance interception, and deterministic delivery semantics.

**Scope distinction:** RFC-001 (JITNA) defines the *negotiation protocol* that
runs on top of IPC. This RFC defines the *transport layer* — message primitives,
routing, delivery guarantees, and mailbox management.

## Motivation

Without IPC, agents can only interact through implicit shared-state mutation
(WorldState resources). This is limiting because:

- **No direct communication** — agents cannot send targeted messages
- **No governance visibility** — state mutation bypasses governance checks
- **No delivery guarantees** — no way to know if an implicit signal was received
- **No audit trail** — no message log for post-simulation analysis

The IPC layer provides explicit, auditable, governance-aware agent communication.

## Specification

### 1. KernelMessage Schema

```python
@dataclass
class KernelMessage:
    msg_id: str                    # Auto-assigned "msg_000001" format
    sender_pid: int                # Sender process ID (0 = kernel/governance)
    receiver_pid: int              # Target process ID (0 = broadcast)
    intent: str = "NEUTRAL"        # Intent context (governance interception key)
    payload: Dict[str, Any]        # Arbitrary dict payload
    priority: MessagePriority      # NORMAL | URGENT | GOVERNANCE_BROADCAST
    sent_tick: int                 # Tick at which message was sent
    expires_at_tick: Optional[int] # TTL (None = no expiry)
    status: MessageStatus          # Delivery status tracking
```

### 2. MessagePriority

| Priority               | Description                                    |
|------------------------|------------------------------------------------|
| `NORMAL`               | Standard agent-to-agent message                |
| `URGENT`               | Priority delivery (future: queue front)        |
| `GOVERNANCE_BROADCAST` | Kernel/governance system message to all agents |

### 3. MessageStatus

| Status                  | Description                          |
|-------------------------|--------------------------------------|
| `PENDING`               | Created, not yet routed              |
| `DELIVERED`             | Successfully placed in receiver mailbox |
| `BLOCKED_BY_GOVERNANCE` | GovernanceInterceptor rejected message |
| `EXPIRED`               | TTL expired or receiver not found    |
| `MAILBOX_FULL`          | Receiver mailbox at capacity         |

### 4. AgentMailbox

Bounded inbox per agent with configurable capacity (default: 50 messages):

| Operation               | Complexity | Description                      |
|--------------------------|-----------|----------------------------------|
| `deliver(msg)`           | O(1)      | Append message (False if full)   |
| `receive_all()`          | O(n)      | Pop all messages                 |
| `receive_by_intent()`    | O(n)      | Pop messages matching intent     |
| `flush()`                | O(1)      | Clear all messages               |
| `oldest_message_age()`   | O(1)      | Age of oldest message in ticks   |

**Bounded capacity** prevents memory exhaustion from message flooding. When the
mailbox is full, new messages are dropped with `MAILBOX_FULL` status.

### 5. GovernanceInterceptor

A callback interface for governance-layer message filtering:

```python
GovernanceInterceptor = Callable[[KernelMessage], Tuple[bool, str]]
# Returns: (allowed: bool, reason: str)
```

Default interceptor allows all messages. Custom interceptors can:
- Block messages from exiled agents
- Block messages violating resource caps
- Block messages with prohibited intent types
- Log intercepted messages for audit

### 6. KernelMessageBus (Central Router)

The bus is the single routing point for all IPC:

```
Sender → Bus.send() → Governance Check → Expiry Check → Mailbox Delivery
```

#### Routing Pipeline

1. **Governance interception** — interceptor callback decides allow/block
2. **Expiry check** — discard if current tick > expires_at_tick
3. **Mailbox lookup** — find receiver's mailbox
4. **Delivery** — append to mailbox (or MAILBOX_FULL if capacity exceeded)

#### Broadcast

`broadcast(sender_pid, intent, payload, tick)` delivers to ALL registered
mailboxes except the sender. Deterministic order (sorted by PID).

### 7. Delivery Guarantees

| Guarantee          | Value                                                |
|--------------------|------------------------------------------------------|
| **Ordering**       | Deterministic by (sent_tick, msg_id)                 |
| **Delivery**       | At-most-once within tick window                      |
| **Durability**     | In-memory only (no persistence across runs)          |
| **Broadcast order**| Sorted by receiver PID (ascending)                   |

### 8. MessageBusMetrics

```python
@dataclass
class MessageBusMetrics:
    total_sent: int = 0          # Messages submitted to bus
    total_delivered: int = 0     # Successfully delivered
    total_blocked: int = 0       # Blocked by governance
    total_expired: int = 0       # Expired (TTL or no receiver)
    total_mailbox_full: int = 0  # Dropped due to full mailbox
    total_broadcasts: int = 0    # Broadcast operations
```

### 9. Message ID Assignment

Message IDs are auto-incremented with format `msg_NNNNNN` (zero-padded 6 digits).
IDs are unique within a single KernelMessageBus instance (per simulation run).

## Test Coverage

25 tests in `tests/kernel/test_ipc.py` covering:

- Message creation and serialization
- Mailbox deliver/receive/flush operations
- Mailbox capacity enforcement (bounded)
- Message bus send with governance allow/block
- TTL expiry semantics
- Broadcast to all registered recipients
- Receiver not found handling
- GovernanceInterceptor callback integration
- MessageBusMetrics accumulation
- Deterministic message ID assignment

## Interaction with Other RFCs

| RFC   | Relationship                                                    |
|-------|-----------------------------------------------------------------|
| RFC-001 | JITNA negotiation messages use IPC as transport layer          |
| RFC-002 | Messages addressed by PID from ProcessTable                    |
| RFC-003 | Messages delivered between scheduler ticks                     |
| RFC-005 | SYS_SEND_MSG syscall wraps IPC send with capability check      |
| RFC-006 | Fault Isolation may deregister faulted agent's mailbox         |

## Backward Compatibility

- **Full backward compatibility.** IPC is an opt-in layer. Simulations can run
  without KernelMessageBus — existing WorldState-based interaction continues
  to work.
- Message bus is created by SimulationEngine if IPC is enabled in config.
