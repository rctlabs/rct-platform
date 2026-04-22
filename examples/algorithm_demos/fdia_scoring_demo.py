"""
RCT Platform — FDIA Scoring Demo
================================
Zero API keys required. Runs fully offline.

Demonstrates the FDIA equation engine:
  F = D^I × A
  F = Future output score (0.0–1.0)
  D = Data quality (0.0–1.0)
  I = Intent precision (acts as exponent)
  A = Architect approval gate (0.0–1.0)

Run:
    pip install -e .
    python examples/algorithm_demos/fdia_scoring_demo.py
"""
from __future__ import annotations
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.fdia.fdia import FDIAScorer, FDIAWeights, NPCAction, NPCIntentType


def main() -> None:
    scorer = FDIAScorer(weights=FDIAWeights())

    scenarios = [
        {
            "label": "High precision intent + positive resource environment",
            "intent": NPCIntentType.DISCOVER,
            "action": NPCAction(
                action_id="demo-001",
                action_type="explore",
                resource_id="knowledge",
                amount=10.0,
                metadata={"strategic_value": 0.9},
            ),
            "resources": {"energy": 80.0, "knowledge": 50.0},
            "reputation": 0.95,
            "other_intents": [NPCIntentType.DISCOVER, NPCIntentType.NEUTRAL],
        },
        {
            "label": "Dominate intent + attack action (high conflict)",
            "intent": NPCIntentType.DOMINATE,
            "action": NPCAction(
                action_id="demo-002",
                action_type="attack",
                target_agent="agent-enemy",
                amount=50.0,
                metadata={"risk_level": 0.9},
            ),
            "resources": {"energy": 30.0},
            "reputation": 0.2,
            "other_intents": [NPCIntentType.PROTECT, NPCIntentType.PROTECT],
        },
        {
            "label": "Trade scenario — accumulate intent + positive alignment",
            "intent": NPCIntentType.ACCUMULATE,
            "action": NPCAction(
                action_id="demo-003",
                action_type="trade",
                target_agent="agent-merchant",
                resource_id="gold",
                amount=15.0,
            ),
            "resources": {"gold": 100.0, "energy": 60.0},
            "reputation": 0.75,
            "other_intents": [NPCIntentType.BELONG, NPCIntentType.ACCUMULATE],
        },
    ]

    print("\n" + "=" * 60)
    print("  RCT PLATFORM — FDIA SCORING DEMO (v1.0.2a0)")
    print("  Equation: F = D^I × A")
    print("=" * 60)

    for i, scenario in enumerate(scenarios, 1):
        score = scorer.score_action(
            agent_intent=scenario["intent"],
            action=scenario["action"],
            world_resources=scenario["resources"],
            agent_reputation=scenario["reputation"],
            other_intents=scenario.get("other_intents"),
        )

        print(f"\n[{i}] {scenario['label']}")
        print(f"    Intent : {scenario['intent'].value}")
        print(f"    Action : {scenario['action'].action_type}")
        print(f"    FDIA Score : {score:.4f}")
        status = "✓ APPROVED" if score >= 0.5 else "✗ BLOCKED"
        print(f"    Outcome: {status}")

    print("\n" + "=" * 60)
    print("  Key insight: When A=0 (Architect = 0), F=0 regardless of D or I.")
    print("  The system NEVER acts without human approval.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
