# Use Case: DevOps & Infrastructure Automation

The RCT Control Plane provides a **constitutional deployment pipeline** — every infrastructure change is compiled into a structured IntentObject, scored by FDIA, evaluated by governance policies, and executed only after passing all gates.

---

## The Problem with Unconstrained Automation

Standard CI/CD pipelines execute whatever the pipeline file says. A misconfiguration, a typo, or a compromised pipeline step can take down production instantly. RCT adds a mandatory governance layer:

```
git push → CI build → RCT compile → FDIA score → Policy evaluate → (Human approve?) → Deploy
```

No step in the deployment path can bypass the governance evaluation.

---

## Full Deployment Pipeline

```python
from rct_control_plane.intent_compiler import IntentCompiler
from rct_control_plane.policy_language import (
    PolicyEvaluator, PolicyRule, PolicyCondition,
    PolicyAction, PolicyPriority, PolicyScope, ConditionOperator,
)
from rct_control_plane.default_policies import (
    create_cost_cap_policy,
    create_risk_escalation_policy,
)
from rct_control_plane.observability import ControlPlaneObserver
from decimal import Decimal

observer = ControlPlaneObserver()
compiler = IntentCompiler(observer=observer)
evaluator = PolicyEvaluator(observer=observer)

# ── Policies ──────────────────────────────────────────────────────────────

# Block production deploys that cost more than $200 (compute cost estimate)
evaluator.register_policy(create_cost_cap_policy(max_cost_usd=Decimal("200.00")))

# Escalate SYSTEMIC risk operations (full infra migrations)
evaluator.register_policy(create_risk_escalation_policy())

# Require approval for any production deployment
evaluator.register_policy(PolicyRule(
    name="Production Deploy Gate",
    description="All production deployments require ops lead approval",
    scope=PolicyScope.INTENT,
    priority=PolicyPriority.HIGH,
    conditions=[
        PolicyCondition(
            field="goal",
            operator=ConditionOperator.CONTAINS,
            value="production",
        )
    ],
    action=PolicyAction.REQUIRE_APPROVAL,
    action_metadata={
        "approver_role": "ops-lead",
        "reason": "Production environment gate",
        "sla_minutes": 30,
    },
))

# ── Compile intent ─────────────────────────────────────────────────────────

result = compiler.compile(
    natural_language="Deploy service payment-api v2.3.1 to production at 14:00 UTC",
    user_id="ci-bot-007",
    user_tier="enterprise",
)

intent = result.intent
print(f"Intent compiled: {intent.id}")
print(f"Intent type    : {intent.intent_type.value}")  # → DEPLOY
print(f"Risk profile   : {intent.risk_profile.value}")

# ── Evaluate ───────────────────────────────────────────────────────────────

eval_result = evaluator.evaluate(intent=intent)

for v in eval_result.violations:
    print(f"[{v.action.value.upper()}] {v.rule_name}: {v.action_metadata.get('reason', '')}")

# Execution only proceeds if no REJECT violations
blocking = [v for v in eval_result.violations if v.action.value == "reject"]
if not blocking:
    print("→ Proceeding to SignedAI approval workflow")
else:
    print("→ Deploy blocked by governance")
```

---

## Equivalent CLI Commands

```bash
# Compile the deployment intent
rct compile "Deploy service payment-api v2.3.1 to production at 14:00 UTC" \
    --user-id ci-bot-007

# Build the execution graph
rct build --intent-id <id>

# Run governance evaluation
rct evaluate --intent-id <id>

# Check status
rct status <id>

# After human approval — audit the approval chain
rct audit <id> --verify
```

See the full interactive walkthrough:

```bash
python examples/cli_walkthrough.py \
    --intent "Deploy service payment-api v2.3.1 to production at 14:00 UTC" \
    --verbose
```

---

## FDIA Scoring for Deployment Actions

The IntentCompiler maps deployment intents to `IntentType.DEPLOY`, which is scored with:

| Scenario | Agent intent (internal) | Expected best action |
|---|---|---|
| Standard deploy | `ACCUMULATE` (deliver value) | `cooperate` (collaborate with ops) |
| Risky deploy (SYSTEMIC) | `ACCUMULATE` | `explore` (canary/blue-green) |
| Emergency rollback | `PROTECT` | `defend` (rollback immediately) |
| Database migration | `DISCOVER` | `explore` (dry-run first) |

---

## Governance Policy Matrix for DevOps

| Environment | Policy | Gate |
|---|---|---|
| Dev / staging | `LOG` | No gate — only audit |
| Production (minor) | `NOTIFY` | Slack alert |
| Production (major) | `REQUIRE_APPROVAL` | Ops lead |
| Full infra migration | `ESCALATE` | CTO + CAB committee |
| Emergency rollback | `APPROVE` | Auto-approved (fast path) |

---

## Audit & Rollback

Every deployment intent is permanently auditable:

```bash
# Verify a past deployment decision
rct audit abc-123 --verify

# Replay a governance evaluation for a specific past deploy
python -m rct.audit.replay --pillar 4 --verbose
# → Confirms deterministic replay guarantee
```

The delta engine records every deployment state change. If a deployment fails, the control plane can replay the pre-deployment state:

```python
from core.delta_engine.memory_delta import MemoryDeltaEngine

engine = MemoryDeltaEngine()
# ... register and record deployment ticks ...

# Rollback to state before the bad deploy
pre_deploy_state = engine.get_state_at_tick("infra_agent", tick=deploy_tick - 1)
engine.rollback("infra_agent", n_ticks=1)
```

---

## Integration with CI/CD

Add RCT governance as a CI stage:

```yaml
# .github/workflows/deploy.yml
- name: RCT Governance Gate
  run: |
    python -c "
    from rct.governance import GovernanceGate
    import sys
    gate = GovernanceGate(fdia_threshold=0.70)
    gate.evaluate('Deploy ${{ env.SERVICE }} to production') or sys.exit(1)
    "
```

---

## See Also

- [Governance Layer](../concepts/governance.md)
- [Finance Use Case](finance.md)
