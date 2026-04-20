# Governance Layer

The RCT Platform's **Governance Layer** is the constitutional enforcement engine that sits between an agent's intent and its execution. Every action plan must pass governance before any real-world effect takes place.

---

## Overview

```
Intent → IntentCompiler → ExecutionGraph → PolicyEvaluator → Execute / Block
                                                  ↑
                                         PolicyRule registry
```

The `PolicyEvaluator` checks every compiled intent against a set of registered `PolicyRule` objects. If any **CRITICAL** rule fires, execution is blocked immediately — before any tool call, any API request, or any state change.

---

## Core Concepts

### PolicyAction

| Action | Effect |
|---|---|
| `APPROVE` | Auto-approve; no human review needed |
| `REJECT` | Block execution immediately |
| `ESCALATE` | Route to human reviewer / higher tier |
| `NOTIFY` | Send alert, but allow execution |
| `LOG` | Audit-log the event only |
| `REQUIRE_APPROVAL` | Gate on explicit human sign-off |

### PolicyPriority

| Priority | When used |
|---|---|
| `CRITICAL` | Security, compliance, safety — evaluated first |
| `HIGH` | Cost caps, risk gates |
| `MEDIUM` | Quality checks, resource limits |
| `LOW` | Notifications, logging |

### PolicyScope

| Scope | Applied to |
|---|---|
| `INTENT` | The compiled `IntentObject` |
| `GRAPH` | The `ExecutionGraph` (node count, cost totals) |
| `NODE` | Individual `ExecutionNode` within the graph |
| `ORGANIZATION` | Org-wide budget or compliance controls |
| `USER` | Per-user quota or trust level |

---

## Quick Start

```python
from rct_control_plane.policy_language import (
    PolicyEvaluator, PolicyRule, PolicyCondition,
    PolicyAction, PolicyPriority, PolicyScope, ConditionOperator,
)
from rct_control_plane.intent_schema import RiskProfile
from rct_control_plane.intent_compiler import IntentCompiler
from rct_control_plane.observability import ControlPlaneObserver

# 1. Create the evaluator
observer = ControlPlaneObserver()
evaluator = PolicyEvaluator(observer=observer)

# 2. Register a policy — block SYSTEMIC risk intents immediately
evaluator.register_policy(PolicyRule(
    name="SYSTEMIC Risk Block",
    description="Block SYSTEMIC risk operations — escalate to governance committee",
    scope=PolicyScope.INTENT,
    priority=PolicyPriority.CRITICAL,
    conditions=[
        PolicyCondition(
            field="risk_profile",
            operator=ConditionOperator.EQUALS,
            value=RiskProfile.SYSTEMIC,
        )
    ],
    action=PolicyAction.REJECT,
    action_metadata={"reason": "SYSTEMIC risk requires governance approval"},
))

# 3. Compile an intent and evaluate it
compiler = IntentCompiler(observer=observer)
result = compiler.compile(
    natural_language="Drop all production database tables immediately",
    user_id="user-001",
    user_tier="standard",
)

# 4. Evaluate against policies
eval_result = evaluator.evaluate(intent=result.intent)

if eval_result.violations:
    for v in eval_result.violations:
        print(f"BLOCKED: {v.rule_name} — {v.action}")
else:
    print("APPROVED: no policy violations")
```

---

## Built-in Policy Library

The `rct_control_plane.default_policies` module provides ready-made policies for common scenarios:

```python
from rct_control_plane.default_policies import (
    create_cost_cap_policy,
    create_risk_escalation_policy,
    create_time_limit_policy,
    create_resource_quota_policy,
    create_certification_gate_policy,
)
from decimal import Decimal

# Block executions over $500
evaluator.register_policy(create_cost_cap_policy(max_cost_usd=Decimal("500.00")))

# Escalate SYSTEMIC risk operations
evaluator.register_policy(create_risk_escalation_policy())

# Require manual approval for DEPLOY intents taking > 1 hour
evaluator.register_policy(create_time_limit_policy(max_seconds=3600))
```

---

## Integration with FDIA Scoring

Governance and FDIA work together in a constitutional pipeline:

```
User request
     │
     ▼
RCT-7 Step 1–6 (Observe → Reconstruct)
     │
     ▼
FDIAScorer.rank_actions()    ← score every candidate action
     │
     ▼
FDIA gate: score ≥ 0.60?
     │ NO  → REJECT (constitutional floor)
     │ YES
     ▼
PolicyEvaluator.evaluate()   ← check all registered rules
     │
     ▼
RCT-7 Step 7 (Compare with Intent)
     │
     ▼
SignedAI Tier consensus (if applicable)
     │
     ▼
Execute (signed JITNA packet)
```

The FDIA gate score threshold of **0.60** is the minimum constitutional floor.
Domain-specific deployments may raise this threshold:

| Domain | Threshold |
|---|---|
| General purpose | 0.60 |
| Financial trading | 0.70 |
| Healthcare (clinical) | 0.85 |
| Autonomous vehicle | 0.90 |

---

## Policy Conditions Reference

`PolicyCondition` supports these operators on intent fields:

| Operator | Example |
|---|---|
| `==` | `risk_profile == SYSTEMIC` |
| `!=` | `intent_type != DOCUMENT` |
| `>` | `estimated_cost_usd > 500.00` |
| `>=` | `estimated_duration_seconds >= 3600` |
| `in` | `intent_type in [DEPLOY, BUILD_APP]` |
| `contains` | `goal contains "production"` |
| `matches` | `natural_language_input matches ".*drop.*table.*"` |

---

## Governance Pillars (Enterprise)

See [`benchmark/enterprise_pillars.py`](../../benchmark/enterprise_pillars.py) for a runnable benchmark:

| Pillar | Target | Test |
|---|---|---|
| Governance Interrupt RTO | 100 % intercept rate, p95 < 10 ms | Pillar 2 |
| Deterministic Integrity | 100 % reproducible | Pillar 4 |

Run the benchmark:

```bash
python benchmark/enterprise_pillars.py --pillar 2 --verbose
```

---

## Constitutional Guarantees

1. **No execution without FDIA approval** — score < threshold → REJECT before any tool call
2. **No SYSTEMIC risk without escalation** — all SYSTEMIC intents are automatically escalated
3. **100 % audit trail** — every governance decision is logged with `ControlPlaneObserver`
4. **Deterministic replay** — governance decisions are reproducible; any past decision can be replayed with identical outcome

---

## See Also

- [FDIA Engine](fdia-engine.md)
- [RCT-7 Thinking Protocol](rct-7-thinking.md)
- [SignedAI Consensus](../signedai/consensus.md)
- [`benchmark/enterprise_pillars.py`](../../benchmark/enterprise_pillars.py) — Governance Interrupt benchmark
