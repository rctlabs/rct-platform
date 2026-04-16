"""
P1-B: Integration Tests — Cross-module workflows.

Tests that verify multiple components work together end-to-end.
No external APIs or databases required.
"""

import pytest
from decimal import Decimal

from rct_control_plane.intent_compiler import IntentCompiler
from rct_control_plane.intent_schema import (
    BudgetSpec,
    ContextBundle,
    IntentObject,
    IntentPriority,
    IntentType,
    RiskProfile,
    ScopeObject,
    ScopeType,
)
from rct_control_plane.policy_language import (
    ConditionOperator,
    PolicyAction,
    PolicyCondition,
    PolicyEvaluator,
    PolicyPriority,
    PolicyRule,
)
from rct_control_plane.control_plane_state import (
    ControlPlanePhase,
    ControlPlaneState,
    TransitionResult,
)
from rct_control_plane.replay_engine import ReplayEngine, compute_execution_hash
from rct_control_plane.observability import ControlPlaneEventType, ControlPlaneObserver
from rct_control_plane.jitna_protocol import (
    JITNAPacket,
    JITNAValidator,
)
from rct_control_plane.signed_execution import (
    SignedExecutionPacket,
    generate_keypair,
    verify_packet,
)


class TestCompileAndEvaluateWorkflow:
    """Compile NL → evaluate against policies → check decision."""

    def test_refactor_approved_for_pro_user(self):
        compiler = IntentCompiler()
        result = compiler.compile("Refactor the auth module", user_id="u1", user_tier="PRO")
        assert result.success

        evaluator = PolicyEvaluator()
        evaluator.add_rule(PolicyRule(
            name="block_free",
            conditions=[PolicyCondition(field="user_tier", operator=ConditionOperator.EQUALS, value="FREE")],
            action=PolicyAction.REJECT,
        ))
        eval_result = evaluator.evaluate_intent(result.intent)
        assert eval_result.decision == PolicyAction.APPROVE

    def test_deploy_blocked_for_free_user(self):
        compiler = IntentCompiler()
        result = compiler.compile("Deploy the application", user_id="free1", user_tier="FREE")
        assert result.success

        evaluator = PolicyEvaluator()
        evaluator.add_rule(PolicyRule(
            name="block_free_deploy",
            conditions=[
                PolicyCondition(field="user_tier", operator=ConditionOperator.EQUALS, value="FREE"),
                PolicyCondition(field="intent_type", operator=ConditionOperator.EQUALS, value=IntentType.DEPLOY),
            ],
            action=PolicyAction.REJECT,
            priority=PolicyPriority.CRITICAL,
        ))
        eval_result = evaluator.evaluate_intent(result.intent)
        assert eval_result.decision == PolicyAction.REJECT


class TestStateAndReplayWorkflow:
    """State transitions → checkpoint → verify hash chain."""

    def test_checkpoint_and_verify_full_lifecycle(self):
        state = ControlPlaneState(intent_id="lifecycle-1")
        engine = ReplayEngine()

        # initial checkpoint
        cp1 = engine.record(state)

        # transition through happy path
        state.transition_to(ControlPlanePhase.INTENT_COMPILED)
        cp2 = engine.record(state)
        state.transition_to(ControlPlanePhase.GRAPH_BUILT)
        cp3 = engine.record(state)

        # verify chain
        chain = engine.verify_chain(state.state_id)
        assert all(r.matches for r in chain)

        # verify latest hash matches
        latest_hash = compute_execution_hash(state)
        assert engine.verify(state, latest_hash).matches is True


class TestObserverWithCompilerIntegration:
    """IntentCompiler emits events to observer → verify metrics."""

    def test_compiler_emits_intent_events(self):
        observer = ControlPlaneObserver()
        compiler = IntentCompiler(observer=observer)
        compiler.compile("Build a REST API", user_id="u1", user_tier="PRO")

        summary = observer.get_metrics_summary()
        assert summary["total_intents"] >= 1
        assert summary["total_compilations"] >= 1


class TestSignedJITNAWorkflow:
    """Create JITNA → Sign → Validate → Verify signature."""

    def test_sign_validate_verify(self):
        private_key, public_key = generate_keypair()
        pkt = JITNAPacket(
            source_agent_id="compiler",
            target_agent_id="executor",
            payload={"intent": "deploy"},
            priority=4,
        )

        # Sign
        signed = SignedExecutionPacket.sign(pkt, private_key, public_key)
        assert signed.signature != ""

        # Validate
        validator = JITNAValidator()
        result = validator.validate(pkt)
        assert result.is_valid is True

        # Verify signature
        assert signed.verify(public_key) is True


class TestPolicyWithObserverIntegration:
    """PolicyEvaluator emits events through observer."""

    def test_policy_evaluation_tracked(self):
        observer = ControlPlaneObserver()
        evaluator = PolicyEvaluator(observer=observer)
        evaluator.add_rule(PolicyRule(
            name="test",
            conditions=[PolicyCondition(field="intent_type", operator=ConditionOperator.EQUALS, value=IntentType.DEPLOY)],
            action=PolicyAction.REJECT,
        ))

        intent = IntentObject(
            goal="Deploy app",
            intent_type=IntentType.DEPLOY,
            scope=ScopeObject(scope_type=ScopeType.MODULE, target="."),
            context=ContextBundle(user_id="u1", user_tier="PRO"),
        )
        evaluator.evaluate_intent(intent)

        summary = observer.get_metrics_summary()
        assert summary["total_policy_evaluations"] == 1
        assert summary["policy_violations"] >= 1


class TestEndToEndCompileStateReplay:
    """Full pipeline: compile → state transition → replay verify."""

    def test_full_pipeline(self):
        compiler = IntentCompiler()
        result = compiler.compile("Refactor module with $5.00 budget", user_id="u1", user_tier="PRO")
        assert result.success

        state = ControlPlaneState(intent_id=str(result.intent.id))
        engine = ReplayEngine()

        engine.record(state)
        state.transition_to(ControlPlanePhase.INTENT_COMPILED)
        engine.record(state)

        chain = engine.verify_chain(state.state_id)
        assert len(chain) == 1
        assert chain[0].matches is True
