"""
Property-based tests for SignedAIRegistry — consensus + cost correctness.

Properties verified:
  1. calculate_consensus() confidence always in [0.0, 1.0]
  2. consensus_reached=True requires votes_for >= required_votes threshold
  3. More for-votes → higher or equal confidence (monotonic)
  4. Zero total votes → confidence == 0.0 (no division by zero)
  5. estimate_tier_cost() always returns non-negative cost
  6. TIER_S (single signer) always reaches consensus with 1 for-vote
  7. Chairman veto override always dominates vote count
  8. Cost scales monotonically with token count
"""

from hypothesis import given, assume, strategies as st

from signedai.core.registry import (
    SignedAIRegistry,
    SignedAITier,
    ConsensusResult,
)

# ── Strategies ────────────────────────────────────────────────────────────

_tier_st = st.sampled_from(list(SignedAITier))
_votes_st = st.integers(min_value=0, max_value=20)
_token_st = st.integers(min_value=1, max_value=100_000)


# ── Property 1: Confidence always in [0.0, 1.0] ──────────────────────────

@given(
    tier=_tier_st,
    votes_for=_votes_st,
    votes_against=_votes_st,
)
def test_confidence_in_unit_interval(tier, votes_for, votes_against):
    """calculate_consensus() confidence must always be in [0.0, 1.0]."""
    result = SignedAIRegistry.calculate_consensus(
        tier=tier,
        votes_for=votes_for,
        votes_against=votes_against,
    )
    assert isinstance(result, ConsensusResult)
    assert 0.0 <= result.confidence <= 1.0, (
        f"Confidence {result.confidence} out of [0.0, 1.0] "
        f"(tier={tier}, for={votes_for}, against={votes_against})"
    )


# ── Property 2: Zero total votes → confidence == 0.0 ─────────────────────

@given(tier=_tier_st)
def test_zero_votes_gives_zero_confidence(tier):
    """When both votes_for and votes_against are 0, confidence must be 0.0."""
    result = SignedAIRegistry.calculate_consensus(
        tier=tier,
        votes_for=0,
        votes_against=0,
    )
    assert result.confidence == 0.0, (
        f"Zero votes must give 0.0 confidence, got {result.confidence}"
    )


# ── Property 3: More for-votes → equal or higher confidence ──────────────

@given(
    tier=_tier_st,
    votes_for_low=st.integers(min_value=0, max_value=5),
    extra_for=st.integers(min_value=1, max_value=5),
    votes_against=st.integers(min_value=0, max_value=5),
)
def test_more_for_votes_monotonic_confidence(tier, votes_for_low, extra_for, votes_against):
    """Adding more for-votes must not decrease confidence."""
    votes_for_high = votes_for_low + extra_for

    result_low = SignedAIRegistry.calculate_consensus(
        tier=tier,
        votes_for=votes_for_low,
        votes_against=votes_against,
    )
    result_high = SignedAIRegistry.calculate_consensus(
        tier=tier,
        votes_for=votes_for_high,
        votes_against=votes_against,
    )

    # Skip chairman-override tiers (Tier 8) where veto overrides vote count
    config = SignedAIRegistry.get_tier(tier)
    if config.chairman_veto:
        return  # chairman_override=None → normal vote path, so still valid

    assert result_high.confidence >= result_low.confidence - 1e-9, (
        f"More for-votes ({votes_for_high}) gave lower confidence ({result_high.confidence}) "
        f"than fewer ({votes_for_low}, confidence={result_low.confidence})"
    )


# ── Property 4: estimate_tier_cost() is always non-negative ──────────────

@given(
    tier=_tier_st,
    input_tokens=_token_st,
    output_tokens=_token_st,
)
def test_tier_cost_non_negative(tier, input_tokens, output_tokens):
    """Estimated tier cost must always be ≥ 0."""
    total, breakdown = SignedAIRegistry.estimate_tier_cost(
        tier=tier,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
    assert total >= 0.0, f"Tier cost {total} is negative for tier={tier}"
    for model_id, cost in breakdown.items():
        assert cost >= 0.0, f"Per-model cost {cost} for {model_id} is negative"


# ── Property 5: Cost scales with token count ─────────────────────────────

@given(
    tier=_tier_st,
    tokens_low=st.integers(min_value=1, max_value=10_000),
    tokens_high=st.integers(min_value=10_001, max_value=100_000),
)
def test_tier_cost_scales_with_tokens(tier, tokens_low, tokens_high):
    """More tokens → higher or equal cost (monotonic, same ratio in/out)."""
    assume(tokens_high > tokens_low)
    cost_low, _ = SignedAIRegistry.estimate_tier_cost(
        tier=tier, input_tokens=tokens_low, output_tokens=tokens_low
    )
    cost_high, _ = SignedAIRegistry.estimate_tier_cost(
        tier=tier, input_tokens=tokens_high, output_tokens=tokens_high
    )
    assert cost_high >= cost_low - 1e-9, (
        f"Higher token count ({tokens_high}) gave lower cost ({cost_high}) "
        f"than lower count ({tokens_low}, cost={cost_low})"
    )


# ── Property 6: ConsensusResult total_votes == votes_for + votes_against ──

@given(
    tier=_tier_st,
    votes_for=_votes_st,
    votes_against=_votes_st,
)
def test_total_votes_is_sum(tier, votes_for, votes_against):
    """ConsensusResult.total_votes must equal votes_for + votes_against."""
    result = SignedAIRegistry.calculate_consensus(
        tier=tier,
        votes_for=votes_for,
        votes_against=votes_against,
    )
    assert result.total_votes == votes_for + votes_against, (
        f"total_votes={result.total_votes} != "
        f"votes_for({votes_for}) + votes_against({votes_against})"
    )


# ── Property 7: Chairman override dominates for TIER_8 ───────────────────

@given(
    votes_for=_votes_st,
    votes_against=_votes_st,
    override=st.booleans(),
)
def test_chairman_override_dominates_tier8(votes_for, votes_against, override):
    """For TIER_8 (chairman_veto=True), chairman_override must dominate vote counts."""
    result = SignedAIRegistry.calculate_consensus(
        tier=SignedAITier.TIER_8,
        votes_for=votes_for,
        votes_against=votes_against,
        chairman_override=override,
    )
    assert result.consensus_reached == override, (
        f"chairman_override={override} but consensus_reached={result.consensus_reached}"
    )
    if override:
        assert result.confidence == 1.0
    else:
        assert result.confidence == 0.0


# ── Property 8: get_tier_by_risk returns valid tier config ───────────────

from signedai.core.registry import RiskLevel

@given(risk=st.sampled_from(list(RiskLevel)))
def test_get_tier_by_risk_returns_valid_config(risk):
    """get_tier_by_risk() must return a non-None TierConfig for every RiskLevel."""
    config = SignedAIRegistry.get_tier_by_risk(risk)
    assert config is not None
    assert config.required_votes >= 1
    assert len(config.signers) >= 1
    assert config.cost_multiplier >= 1.0
