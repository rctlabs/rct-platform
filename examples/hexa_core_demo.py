#!/usr/bin/env python3
"""
RCT Hexa-Core Architecture Demo

Demonstrates:
1. All 6 Hexa-Core models
2. Model capabilities and pricing
3. SignedAI consensus routing by risk level
4. SignedAI tier cost comparison
5. Geopolitical balance
6. Specialist capabilities
7. Performance rankings
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from signedai.core.registry import (
    HexaCoreRole,
    HexaCoreRegistry,
    SignedAITier,
    RiskLevel,
    SignedAIRegistry,
)
from signedai.core.router import TierRouter


def print_header(text: str):
    """Print formatted header."""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")


def demo_all_models():
    """Display all 6 Hexa-Core models."""
    print_header("RCT HEXA-CORE ARCHITECTURE - ALL MODELS")
    
    for i, (role, model) in enumerate(HexaCoreRegistry.MODELS.items(), 1):
        print(f"{i}. {role.value.upper().replace('_', ' ')}")
        print(f"   Model: {model.id}")
        print(f"   Provider: {model.provider} ({model.country})")
        print(f"   Pricing: ${model.cost_input:.2f} / ${model.cost_output:.2f} per 1M tokens")
        print(f"   Context: {model.context_window:,} tokens")
        print(f"   Specialties: {', '.join(model.specialties[:3])}")
        
        if model.programming_rank:
            print(f"   Programming Rank: #{model.programming_rank}")
        if model.reasoning_rank:
            print(f"   Reasoning Rank: #{model.reasoning_rank}")
        
        print(f"   Use Cases: {', '.join(model.use_cases[:2])}")
        print()


def demo_geopolitical_balance():
    """Demonstrate geopolitical balance."""
    print_header("GEOPOLITICAL BALANCE")
    
    balance = HexaCoreRegistry.get_geopolitical_balance()
    
    print("Model Distribution:")
    for country, count in balance.items():
        print(f"  {country}: {count} models")
    
    print("\nWest (US) Models:")
    us_models = HexaCoreRegistry.get_models_by_country("US")
    for model in us_models:
        print(f"  • {model.id} ({model.role.value})")
    
    print("\nEast (CN) Models:")
    cn_models = HexaCoreRegistry.get_models_by_country("CN")
    for model in cn_models:
        print(f"  • {model.id} ({model.role.value})")
    
    print(f"\n✅ Balance: {balance['US']} West + {balance['CN']} East = Perfect parity")


def demo_signedai_routing():
    """Demonstrate SignedAI tier selection by risk level."""
    print_header("SIGNEDAI CONSENSUS ROUTING")

    examples = [
        (RiskLevel.LOW, "Chat response, low-stakes query"),
        (RiskLevel.MEDIUM, "Code review, API design decision"),
        (RiskLevel.HIGH, "Production deployment, DB migration"),
        (RiskLevel.CRITICAL, "Critical infrastructure change"),
    ]

    for risk, description in examples:
        tier_cfg = SignedAIRegistry.get_tier_by_risk(risk)
        print(f"Task: {description}")
        print(f"  Risk: {risk.value}")
        print(f"  → Tier: {tier_cfg.tier.value}  ({len(tier_cfg.signers)} signers, {tier_cfg.required_votes} votes required)")
        result = SignedAIRegistry.calculate_consensus(
            tier_cfg.tier,
            votes_for=tier_cfg.required_votes,
            votes_against=len(tier_cfg.signers) - tier_cfg.required_votes,
        )
        print(f"  → Consensus: {result.consensus_reached}, confidence={result.confidence:.0%}")
        print()


def demo_tier_cost():
    """Demonstrate SignedAI tier cost estimation."""
    print_header("SIGNEDAI TIER COST COMPARISON")

    tokens_in = 10_000
    tokens_out = 5_000
    print(f"Token count: {tokens_in:,} input + {tokens_out:,} output\n")

    tiers = [
        SignedAITier.TIER_S,
        SignedAITier.TIER_4,
        SignedAITier.TIER_6,
        SignedAITier.TIER_8,
    ]

    costs = []
    for tier in tiers:
        total, breakdown = SignedAIRegistry.estimate_tier_cost(tier, tokens_in, tokens_out)
        costs.append(total)
        cfg = SignedAIRegistry.get_tier(tier)
        print(f"{tier.value.upper()} ({len(cfg.signers)} signers): ${total:.4f}")
        print(f"  Breakdown: {', '.join(f"{m[:12]}: ${c:.4f}" for m, c in list(breakdown.items())[:2])} ...")
        print()

    tier_s_cost = costs[0]
    tier_8_cost = costs[3]
    overhead = ((tier_8_cost - tier_s_cost) / tier_8_cost) * 100
    print(f"TIER_S vs TIER_8 overhead: {overhead:.1f}% of TIER_8 cost is the consensus premium")
    print(f"✅ Strategy: Use TIER_S for chat, TIER_8 for critical infrastructure.")


def demo_specialist_capabilities():
    """Demonstrate specialist model capabilities."""
    print_header("SPECIALIST MODELS - DOMAIN EXPERTISE")
    
    specialists = [
        (HexaCoreRole.SPECIALIST, "Finance & Health #1"),
        (HexaCoreRole.LIBRARIAN, "Long Context (2M tokens), Science #1"),
        (HexaCoreRole.HUMANIZER, "Roleplay #1, Natural Language")
    ]
    
    for role, expertise in specialists:
        model = HexaCoreRegistry.get_model(role)
        print(f"{role.value.upper().replace('_', ' ')}")
        print(f"  Expertise: {expertise}")
        print(f"  Model: {model.id}")
        print(f"  Best for: {', '.join(model.use_cases[:3])}")
        print()


def demo_ranking_summary():
    """Display ranking summary."""
    print_header("PERFORMANCE RANKINGS")
    
    print("Programming #1 (Tied):")
    print(f"  • Supreme Architect: {HexaCoreRegistry.get_model_id(HexaCoreRole.SUPREME_ARCHITECT)}")
    print(f"  • Lead Builder: {HexaCoreRegistry.get_model_id(HexaCoreRole.LEAD_BUILDER)}")
    print()
    
    print("Programming #2:")
    print(f"  • Junior Builder: {HexaCoreRegistry.get_model_id(HexaCoreRole.JUNIOR_BUILDER)}")
    print()
    
    print("Reasoning #1:")
    architect = HexaCoreRegistry.get_model(HexaCoreRole.SUPREME_ARCHITECT)
    print(f"  • Supreme Architect: {architect.id}")
    print()
    
    print("Reasoning #2:")
    humanizer = HexaCoreRegistry.get_model(HexaCoreRole.HUMANIZER)
    print(f"  • Humanizer: {humanizer.id}")
    print()
    
    print("Context Window King:")
    librarian = HexaCoreRegistry.get_longest_context()
    print(f"  • Librarian: {librarian.id} ({librarian.context_window:,} tokens)")
    print()
    
    print("Cost Champion:")
    junior = HexaCoreRegistry.get_cheapest_coder()
    print(f"  • Junior Builder: ${junior.cost_input}/{junior.cost_output} per 1M tokens")


def main():
    """Run all demos."""
    print("\n" + "🌟" * 35)
    print(" " * 10 + "RCT HEXA-CORE ARCHITECTURE DEMO")
    print("🌟" * 35)
    
    demo_all_models()
    demo_geopolitical_balance()
    demo_signedai_routing()
    demo_tier_cost()
    demo_specialist_capabilities()
    demo_ranking_summary()
    
    print("\n" + "="*70)
    print("  Demo Complete! 🚀")
    print("  For API usage, see: examples/api_usage_demo.py")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
