# Use Case: Finance & Autonomous Trading Governance

The RCT Platform adds a **constitutional governance layer** to autonomous financial agents. Every trade order, rebalance decision, or risk action passes through FDIA scoring and policy gates before execution.

---

## Why RCT for Finance?

Autonomous trading systems fail when they have no constitutional constraint — flash crashes, runaway algos, and compliance violations all stem from unconstrained execution. RCT enforces:

1. **Intent-aligned scoring** — ACCUMULATE-intent agents are scored against desired outcomes, not just immediate P&L
2. **Governance gates** — orders above a threshold require human sign-off (Tier-6 consensus)
3. **Audit trail** — every decision is cryptographically linked and replayable
4. **Deterministic replay** — regulators can re-run any past decision with identical output

---

## Risk-Tiered Order Routing

```python
from core.fdia.fdia import FDIAScorer, FDIAWeights, NPCAction, NPCIntentType

scorer = FDIAScorer(weights=FDIAWeights(
    desire=0.40,
    intent=0.30,
    alignment=0.20,
    governance=0.10,
))

def evaluate_order(
    order_type: str,   # "buy_bond", "buy_crypto", "stop_loss", "hold_cash"
    amount_usd: float,
    portfolio_risk: float,  # 0.0 = low risk, 1.0 = max risk
) -> tuple:
    """Score a financial action against a conservative PROTECT intent."""

    investment_actions = [
        NPCAction("buy_bond",   "trade",   amount=amount_usd,   resource_id="bonds"),
        NPCAction("buy_crypto", "trade",   amount=amount_usd,   resource_id="crypto"),
        NPCAction("stop_loss",  "defend",  amount=amount_usd,   resource_id="portfolio"),
        NPCAction("hold_cash",  "idle",    amount=0.0),
    ]

    # Conservative investor: PROTECT intent
    ranked = scorer.rank_actions(
        agent_intent=NPCIntentType.PROTECT,
        actions=investment_actions,
        world_resources={"bonds": 5_000_000.0, "crypto": 200_000.0, "portfolio": 1_000_000.0},
        agent_reputation=max(0.1, 1.0 - portfolio_risk),
        governance_penalties={
            "buy_crypto": 0.30 if portfolio_risk > 0.7 else 0.0,  # penalise crypto in high-risk env
        } if portfolio_risk > 0.7 else None,
    )
    return ranked

# Example: risky market environment
orders = evaluate_order("buy_bond", 100_000.0, portfolio_risk=0.8)
best, score = orders[0]
print(f"Best action: {best.action_id} (score: {score:.4f})")
# → stop_loss or buy_bond (PROTECT intent + safe instrument = high score)
```

---

## Governance Gates by Order Size

| Order size | Tier | Approvers | Threshold |
|---|---|---|---|
| < $10,000 | Tier-S | Auto-approve | n/a |
| $10k – $1M | Tier-4 | 3 of 4 | 75% |
| $1M – $10M | Tier-6 | 4 of 6 | 67% |
| > $10M | Tier-8 | 5 of 8 | 63% + chairman veto |

```python
from signedai.core.registry import SignedAIRegistry, SignedAITier

def get_tier_for_amount(amount_usd: float) -> SignedAITier:
    if amount_usd < 10_000:
        return SignedAITier.TIER_S
    elif amount_usd < 1_000_000:
        return SignedAITier.TIER_4
    elif amount_usd < 10_000_000:
        return SignedAITier.TIER_6
    else:
        return SignedAITier.TIER_8

tier = get_tier_for_amount(2_500_000.0)   # → TIER_6
calc = SignedAIRegistry.calculate_consensus(tier, votes_for=4, votes_against=2)
print(f"Consensus: {calc.passed}")  # True — 4 ≥ threshold of 4
```

---

## Policy: Block High-Risk Deploys

```python
from rct_control_plane.default_policies import create_cost_cap_policy, create_risk_escalation_policy
from decimal import Decimal

# Block any automated action costing > $1M without human approval
evaluator.register_policy(create_cost_cap_policy(max_cost_usd=Decimal("1000000.00")))

# Escalate SYSTEMIC risk (e.g., full portfolio rebalance during market crash)
evaluator.register_policy(create_risk_escalation_policy())
```

---

## Audit & Compliance

Every scored action produces a deterministic record:

```bash
rct compile "Buy $2.5M in US 10-year Treasuries" --user-id trader-007
rct evaluate --intent-id <id>
rct audit    <id> --verify  # cryptographic chain verification
```

The audit chain uses Ed25519-signed JITNA packets. Any past decision can be replayed with:

```bash
python -m rct.audit.replay --pillar 4 --verbose
# → Confirms 100% deterministic replay (Pillar 4)
```

---

## FDIA Score Threshold for Finance

| Decision type | Minimum FDIA score |
|---|---|
| Routine order | 0.65 |
| Large order (> $1M) | 0.70 |
| Systemic risk action | 0.80 |
| Emergency stop-loss | 0.60 (lower — fast path) |

---

## See Also

- [Governance Layer](../concepts/governance.md)
- [SignedAI Consensus](../concepts/signedai.md)
- [FDIA Engine](../concepts/fdia.md)
