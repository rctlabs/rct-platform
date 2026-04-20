# Use Case: Healthcare — Clinical Decision Support

The RCT Platform can serve as a constitutional AI layer for clinical decision support systems (CDSS), ensuring that AI recommendations are governed, auditable, and always escalated to human clinicians for high-stakes decisions.

---

## Constitutional Principles for Healthcare AI

1. **AI recommends, humans decide** — FDIA scoring ranks options; final execution requires Tier-8 consensus (5 of 8 clinicians for life-critical decisions)
2. **Higher FDIA threshold** — medical decisions require score ≥ 0.85 (vs 0.60 default)
3. **Deterministic audit** — every recommendation is replayable for liability review
4. **PROTECT intent enforced** — all clinical agents have `NPCIntentType.PROTECT` as constitutional base

---

## Emergency Department Triage

```python
from core.fdia.fdia import FDIAScorer, FDIAWeights, NPCAction, NPCIntentType

scorer = FDIAScorer(weights=FDIAWeights(
    desire=0.35,
    intent=0.35,    # higher intent weight for medical — alignment matters more
    alignment=0.20,
    governance=0.10,
))

MEDICAL_FDIA_THRESHOLD = 0.85  # stricter than default 0.60

def triage_patient(
    vital_severity: float,    # 0.0–1.0 (1.0 = critical)
    available_icu_beds: int,
    patient_age: int,
) -> tuple:
    """Rank clinical actions for a presenting patient."""

    # Resources represent capacity / availability
    world_resources = {
        "icu_beds":     float(available_icu_beds),
        "observation":  10.0,
        "medications":  100.0,
    }

    clinical_actions = [
        NPCAction("admit_icu",       "cooperate", amount=1.0,   resource_id="icu_beds"),
        NPCAction("admit_obs",       "explore",   amount=1.0,   resource_id="observation"),
        NPCAction("prescribe_meds",  "trade",     amount=500.0, resource_id="medications"),
        NPCAction("discharge",       "idle",      amount=0.0),
    ]

    # PROTECT intent — always. Severity affects reputation (trust in urgency signals)
    agent_reputation = 0.60 + vital_severity * 0.40  # 0.60–1.00

    ranked = scorer.rank_actions(
        agent_intent=NPCIntentType.PROTECT,
        actions=clinical_actions,
        world_resources=world_resources,
        agent_reputation=agent_reputation,
    )

    # Filter by medical threshold
    approved = [(a, s) for a, s in ranked if s >= MEDICAL_FDIA_THRESHOLD]
    return approved, ranked

# Critical patient, 2 ICU beds available
approved, all_ranked = triage_patient(vital_severity=0.95, available_icu_beds=2, patient_age=67)

print("Approved recommendations (score ≥ 0.85):")
for action, score in approved:
    print(f"  {action.action_id:20s} {score:.4f}")

print("\nFull ranking:")
for action, score in all_ranked:
    gate = "✓" if score >= MEDICAL_FDIA_THRESHOLD else "✗"
    print(f"  {gate} {action.action_id:20s} {score:.4f}")
```

---

## Tier-8 Consensus for Life-Critical Decisions

For any action scoring ≥ 0.85, a Tier-8 consensus vote must be collected before execution:

```python
from signedai.core.registry import SignedAIRegistry, SignedAITier

# Tier-8: 8 signers, need 5 approvals
calc = SignedAIRegistry.calculate_consensus(
    tier=SignedAITier.TIER_8,
    votes_for=6,
    votes_against=2,
)
print(f"Consensus passed: {calc.passed}")    # True — 6 ≥ 5
print(f"Quorum: {calc.threshold}/{calc.total_signers}")
```

---

## Clinical Scenarios

### Scenario A: ICU Admission (Critical)

- `vital_severity = 0.95` → reputation = 0.98
- `available_icu_beds = 2` → `icu_beds` resource available
- Expected best action: `admit_icu` (PROTECT + cooperate + critical severity)
- FDIA score: ~0.91–0.94 → above 0.85 threshold → approved

### Scenario B: Stable Patient

- `vital_severity = 0.20` → reputation = 0.68
- All ICU beds full (`available_icu_beds = 0`)
- Expected best action: `admit_obs` or `prescribe_meds`
- `admit_icu` constrained by zero resource → `cooperate` action penalised

### Scenario C: Discharge Consideration

- `vital_severity = 0.05` → reputation = 0.62
- Expected: `discharge` (idle) competes with `prescribe_meds`
- FDIA score for `discharge` may fall below 0.85 → requires human override

---

## Governance Policy: Discharge Requires Clinician Approval

```python
from rct_control_plane.policy_language import (
    PolicyEvaluator, PolicyRule, PolicyCondition,
    PolicyAction, PolicyPriority, PolicyScope, ConditionOperator,
)
from rct_control_plane.observability import ControlPlaneObserver

evaluator = PolicyEvaluator(observer=ControlPlaneObserver())

# Block automatic discharge — require explicit clinician sign-off
evaluator.register_policy(PolicyRule(
    name="Discharge Safety Gate",
    description="All discharge decisions require attending physician approval",
    scope=PolicyScope.INTENT,
    priority=PolicyPriority.CRITICAL,
    conditions=[
        PolicyCondition(
            field="goal",
            operator=ConditionOperator.CONTAINS,
            value="discharge",
        )
    ],
    action=PolicyAction.REQUIRE_APPROVAL,
    action_metadata={
        "approver_role": "attending_physician",
        "reason": "Patient safety: discharge must be physician-authorised",
    },
))
```

---

## Audit for Liability

Every clinical recommendation is stored with a deterministic audit trail:

```bash
rct compile "Discharge patient 4721 from ICU" --user-id cdss-agent
rct evaluate --intent-id <id>   # → REQUIRE_APPROVAL fired
rct audit    <id>               # → full chain with attending physician vote
```

---

## Key Differences from Default Configuration

| Parameter | Default | Healthcare |
|---|---|---|
| FDIA threshold | 0.60 | 0.85 |
| Primary intent | varies | Always PROTECT |
| Discharge policy | none | REQUIRE_APPROVAL |
| SignedAI tier | Tier-S or Tier-4 | Tier-8 for life-critical |
| Audit retention | standard | Long-term (liability) |

---

## See Also

- [FDIA Engine](../concepts/fdia-engine.md)
- [Governance Layer](../concepts/governance.md)
- [SignedAI Consensus](../signedai/consensus.md)
- [Finance Use Case](finance.md)
