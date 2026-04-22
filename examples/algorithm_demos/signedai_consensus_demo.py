"""
RCT Platform — SignedAI Multi-LLM Consensus Demo
================================================
Zero API keys required. Runs fully offline with mock LLM providers.

Demonstrates:
  - TIER_S through TIER_8 consensus configurations
  - Constitutional blocking when Architect score = 0
  - HexaCore model registry (7 models)
  - Risk-tier routing: LOW → TIER_S, MEDIUM → TIER_4, HIGH → TIER_6, CRITICAL → TIER_8

Run:
    pip install -e .
    python examples/algorithm_demos/signedai_consensus_demo.py
"""
from __future__ import annotations
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from signedai.core.registry import (
    SignedAIRegistry, SignedAITier, RiskLevel,
    HexaCoreRegistry, HexaCoreRole,
)


def main() -> None:
    print("\n" + "=" * 65)
    print("  RCT PLATFORM — SIGNEDAI CONSENSUS DEMO (v1.0.2a0)")
    print("  Constitutional multi-LLM governance — zero API keys")
    print("=" * 65)

    # Show HexaCore model registry
    print("\n  [HexaCore Model Registry]")
    for role in HexaCoreRole:
        model_id = HexaCoreRegistry.get_model_id(role)
        model = HexaCoreRegistry.get_model(role)
        print(f"  {role.value:<25} {model_id:<40} {model.provider}")

    # Show tier configurations
    print("\n  [Consensus Tier Configuration by Risk Level]")
    tier_scenarios = [
        (RiskLevel.LOW,      SignedAITier.TIER_S, "Routine intent — low risk"),
        (RiskLevel.MEDIUM,   SignedAITier.TIER_4, "Moderate risk — 4-model consensus"),
        (RiskLevel.HIGH,     SignedAITier.TIER_6, "High-stakes — 6-model consensus"),
        (RiskLevel.CRITICAL, SignedAITier.TIER_8, "CRITICAL — 8 signers + chairman veto"),
    ]

    for risk_level, tier, label in tier_scenarios:
        config = SignedAIRegistry.get_tier_by_risk(risk_level)
        print(f"\n  Risk: {risk_level.value.upper():<10} → Tier {tier.value}")
        print(f"    Scenario   : {label}")
        print(f"    Signers    : {len(config.signers)} ({[r.value for r in config.signers]})")
        print(f"    Required   : {config.required_votes}/{len(config.signers)} votes")
        print(f"    Chairman   : {'YES (veto power)' if config.chairman_veto else 'no'}")

    # Calculate consensus result
    print("\n  [Consensus Calculation Example — TIER_4, 3 for / 1 against]")
    result = SignedAIRegistry.calculate_consensus(
        tier=SignedAITier.TIER_4,
        votes_for=3,
        votes_against=1,
    )
    print(f"  Consensus reached: {result.consensus_reached}")
    print(f"  Confidence:        {result.confidence:.0%}")
    print(f"  Cost:              ${result.cost_usd:.4f}")
    print(f"  Signers:           {result.signers}")

    # Constitutional guarantee demo
    print("\n  [Constitutional Guarantee: F = D^I × A]")
    print("  When Architect (A) = 0 → output is ALWAYS blocked regardless of D or I")
    print()
    scenarios = [
        ("High data, high intent, A=0.0", 0.95, 0.9, 0.0),
        ("Perfect data + intent, A=0.0",  1.00, 1.0, 0.0),
        ("Perfect data + intent, A=1.0",  1.00, 1.0, 1.0),
    ]
    for label, D, I, A in scenarios:
        F = (D ** I) * A
        status = "✓ APPROVED" if F > 0 else "✗ BLOCKED"
        print(f"  D={D:.1f}, I={I:.1f}, A={A:.1f} → F={F:.4f}  {status}  ({label})")

    print("\n" + "=" * 65 + "\n")


if __name__ == "__main__":
    main()

