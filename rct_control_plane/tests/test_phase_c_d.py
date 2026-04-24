"""
Phase C & D Tests — replay_engine, jitna_protocol, observability,
signed_execution, middleware, default_policies.

All pure unit tests with no external I/O.
"""

import sys
from decimal import Decimal
from pathlib import Path

import pytest

from rct_control_plane.control_plane_state import (
    ControlPlanePhase,
    ControlPlaneState,
    TransitionResult,
)
from rct_control_plane.default_policies import (
    create_approval_workflow_policy,
    create_certification_gate_policy,
    create_compliance_check_policy,
    create_cost_cap_policy,
    create_custom_policy,
    create_data_sensitivity_policy,
    create_resource_quota_policy,
    create_risk_escalation_policy,
    create_time_limit_policy,
    get_default_policies,
)
from rct_control_plane.jitna_protocol import (
    JITNAMessageType,
    JITNAPacket as ControlPlaneJITNAPacket,
    JITNAStatus,
    JITNAValidator,
)
from rct_control_plane.jitna_protocol import JITNAPacket as JITNAPacketCP
from rct_control_plane.middleware import (
    FeatureFlagStore,
    FlagDefinition,
)
from rct_control_plane.observability import (
    AuditEntry,
    AuditTrail,
    ControlPlaneEvent,
    ControlPlaneEventType,
    ControlPlaneObserver,
)
from rct_control_plane.policy_language import PolicyAction, PolicyRule
from rct_control_plane.replay_engine import (
    Checkpoint,
    ReplayEngine,
    ReplayResult,
    compute_execution_hash,
)
from rct_control_plane.signed_execution import (
    SignedExecutionPacket,
    compute_key_fingerprint,
    generate_keypair,
    sign_packet,
    verify_packet,
)

# ensure benchmark directory is importable for D-3 tests
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


# ===================================================================
# C-1: Replay Engine
# ===================================================================


class TestReplayEngine:
    def setup_method(self):
        self.engine = ReplayEngine()

    def _make_state(self, intent_id: str = "i1") -> ControlPlaneState:
        return ControlPlaneState(intent_id=intent_id)

    def test_compute_hash_deterministic(self):
        state = self._make_state()
        h1 = compute_execution_hash(state)
        h2 = compute_execution_hash(state)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex

    def test_hash_changes_after_transition(self):
        state = self._make_state()
        h_before = compute_execution_hash(state)
        state.transition_to(ControlPlanePhase.INTENT_COMPILED)
        h_after = compute_execution_hash(state)
        assert h_before != h_after

    def test_record_returns_checkpoint(self):
        state = self._make_state()
        cp = self.engine.record(state)
        assert isinstance(cp, Checkpoint)
        assert cp.intent_id == "i1"
        assert cp.version == state.version

    def test_verify_matching_hash(self):
        state = self._make_state()
        expected = compute_execution_hash(state)
        result = self.engine.verify(state, expected)
        assert result.matches is True

    def test_verify_mismatched_hash(self):
        state = self._make_state()
        result = self.engine.verify(state, "0" * 64)
        assert result.matches is False

    def test_get_checkpoints_returns_history(self):
        state = self._make_state()
        self.engine.record(state)
        state.transition_to(ControlPlanePhase.INTENT_COMPILED)
        self.engine.record(state)
        cps = self.engine.get_checkpoints(state.state_id)
        assert len(cps) == 2

    def test_get_latest_checkpoint(self):
        state = self._make_state()
        self.engine.record(state)
        state.transition_to(ControlPlanePhase.INTENT_COMPILED)
        self.engine.record(state)
        latest = self.engine.get_latest_checkpoint(state.state_id)
        assert latest.phase == ControlPlanePhase.INTENT_COMPILED.value

    def test_lookup_by_hash(self):
        state = self._make_state()
        cp = self.engine.record(state)
        sid = self.engine.lookup_by_hash(cp.execution_hash)
        assert sid == state.state_id

    def test_verify_chain_consistent(self):
        state = self._make_state()
        self.engine.record(state)
        state.transition_to(ControlPlanePhase.INTENT_COMPILED)
        self.engine.record(state)
        results = self.engine.verify_chain(state.state_id)
        assert len(results) == 1
        assert results[0].matches is True

    def test_export_checkpoints(self):
        state = self._make_state()
        self.engine.record(state)
        export = self.engine.export_checkpoints()
        assert state.state_id in export

    def test_clear_removes_all(self):
        state = self._make_state()
        self.engine.record(state)
        self.engine.clear()
        assert self.engine.get_checkpoint_count() == 0

    def test_checkpoint_to_dict(self):
        state = self._make_state()
        cp = self.engine.record(state)
        d = cp.to_dict()
        assert "execution_hash" in d
        assert "state_id" in d

    def test_replay_result_to_dict(self):
        r = ReplayResult(matches=True, expected_hash="a", actual_hash="a")
        d = r.to_dict()
        assert d["matches"] is True


# ===================================================================
# C-2: JITNA Protocol — Validator
# ===================================================================


class TestJITNAValidator:
    def setup_method(self):
        self.validator = JITNAValidator()

    def _make_packet(self, **overrides) -> ControlPlaneJITNAPacket:
        defaults = dict(
            source_agent_id="agent-a",
            target_agent_id="agent-b",
            message_type=JITNAMessageType.INTENT_REQUEST.value,
            payload={"action": "test"},
            priority=3,
        )
        defaults.update(overrides)
        return ControlPlaneJITNAPacket(**defaults)

    def test_valid_packet_passes(self):
        result = self.validator.validate(self._make_packet())
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_empty_source_agent_fails(self):
        result = self.validator.validate(self._make_packet(source_agent_id=""))
        assert result.is_valid is False

    def test_wrong_schema_version_fails(self):
        pkt = self._make_packet()
        pkt.schema_version = "1.0"
        result = self.validator.validate(pkt)
        assert result.is_valid is False

    def test_invalid_message_type_fails(self):
        result = self.validator.validate(self._make_packet(message_type="bogus"))
        assert result.is_valid is False

    def test_priority_out_of_range_fails(self):
        result = self.validator.validate(self._make_packet(priority=0))
        assert result.is_valid is False
        result = self.validator.validate(self._make_packet(priority=6))
        assert result.is_valid is False

    def test_empty_payload_warning(self):
        result = self.validator.validate(self._make_packet(payload={}))
        assert any("empty payload" in w for w in result.warnings)

    def test_missing_correlation_id_warning(self):
        result = self.validator.validate(self._make_packet())
        assert any("correlation_id" in w for w in result.warnings)

    def test_compute_hash_deterministic(self):
        pkt = self._make_packet()
        h1 = pkt.compute_hash()
        h2 = pkt.compute_hash()
        assert h1 == h2
        assert len(h1) == 64

    def test_to_json_roundtrip(self):
        pkt = self._make_packet()
        j = pkt.to_json()
        assert '"source_agent_id"' in j
        assert '"agent-a"' in j

    def test_packet_status_default_created(self):
        pkt = self._make_packet()
        assert pkt.status == JITNAStatus.CREATED.value


# ===================================================================
# C-3: ControlPlaneState — extended
# ===================================================================


class TestControlPlaneStateExtended:
    def test_full_happy_path(self):
        """Walk through INTENT_RECEIVED → COMPLETED."""
        state = ControlPlaneState(intent_id="full")
        transitions = [
            ControlPlanePhase.INTENT_COMPILED,
            ControlPlanePhase.GRAPH_BUILT,
            ControlPlanePhase.POLICY_CHECKED,
            ControlPlanePhase.APPROVED,
            ControlPlanePhase.EXECUTING,
            ControlPlanePhase.COMPLETED,
        ]
        for phase in transitions:
            assert state.transition_to(phase) == TransitionResult.SUCCESS
        assert state.phase == ControlPlanePhase.COMPLETED

    def test_is_terminal_completed(self):
        state = ControlPlaneState(intent_id="t1")
        state.transition_to(ControlPlanePhase.INTENT_COMPILED)
        state.transition_to(ControlPlanePhase.GRAPH_BUILT)
        state.transition_to(ControlPlanePhase.POLICY_CHECKED)
        state.transition_to(ControlPlanePhase.APPROVED)
        state.transition_to(ControlPlanePhase.EXECUTING)
        state.transition_to(ControlPlanePhase.COMPLETED)
        assert state.is_terminal() is True

    def test_is_terminal_failed(self):
        state = ControlPlaneState(intent_id="t2")
        state.transition_to(ControlPlanePhase.FAILED)
        assert state.is_terminal() is True

    def test_version_increments(self):
        state = ControlPlaneState(intent_id="v1")
        initial = state.version
        state.transition_to(ControlPlanePhase.INTENT_COMPILED)
        assert state.version == initial + 1

    def test_transitions_recorded(self):
        state = ControlPlaneState(intent_id="tr1")
        state.transition_to(ControlPlanePhase.INTENT_COMPILED)
        assert len(state.transitions) >= 1
        t = state.transitions[-1]
        assert t.to_phase == ControlPlanePhase.INTENT_COMPILED

    def test_to_dict_from_dict_roundtrip(self):
        state = ControlPlaneState(intent_id="rd1")
        state.transition_to(ControlPlanePhase.INTENT_COMPILED)
        d = state.to_dict()
        restored = ControlPlaneState.from_dict(d)
        assert restored.intent_id == "rd1"
        assert restored.phase == ControlPlanePhase.INTENT_COMPILED

    def test_cannot_leave_terminal(self):
        state = ControlPlaneState(intent_id="term")
        state.transition_to(ControlPlanePhase.FAILED)
        result = state.transition_to(ControlPlanePhase.EXECUTING)
        assert result == TransitionResult.INVALID_TRANSITION

    def test_state_id_unique(self):
        s1 = ControlPlaneState(intent_id="x")
        s2 = ControlPlaneState(intent_id="x")
        assert s1.state_id != s2.state_id


# ===================================================================
# C-4: Observability
# ===================================================================


class TestAuditTrail:
    def test_append_creates_entry(self):
        trail = AuditTrail()
        event = ControlPlaneEvent(event_type=ControlPlaneEventType.INTENT_RECEIVED, intent_id="a1")
        entry = trail.append(event)
        assert isinstance(entry, AuditEntry)
        assert entry.entry_hash is not None

    def test_verify_integrity_empty(self):
        trail = AuditTrail()
        assert trail.verify_integrity() is True

    def test_verify_integrity_multiple_entries(self):
        trail = AuditTrail()
        for _ in range(5):
            trail.append(ControlPlaneEvent(event_type=ControlPlaneEventType.INTENT_COMPILED))
        assert trail.verify_integrity() is True

    def test_tampered_entry_detected(self):
        trail = AuditTrail()
        trail.append(ControlPlaneEvent(event_type=ControlPlaneEventType.INTENT_RECEIVED))
        trail.append(ControlPlaneEvent(event_type=ControlPlaneEventType.INTENT_COMPILED))
        # tamper with first entry hash
        trail.entries[0].entry_hash = "deadbeef" * 8
        assert trail.verify_integrity() is False

    def test_get_events_for_intent(self):
        trail = AuditTrail()
        trail.append(ControlPlaneEvent(event_type=ControlPlaneEventType.INTENT_RECEIVED, intent_id="x1"))
        trail.append(ControlPlaneEvent(event_type=ControlPlaneEventType.INTENT_COMPILED, intent_id="x2"))
        events = trail.get_events_for_intent("x1")
        assert len(events) == 1

    def test_get_events_by_type(self):
        trail = AuditTrail()
        trail.append(ControlPlaneEvent(event_type=ControlPlaneEventType.INTENT_RECEIVED))
        trail.append(ControlPlaneEvent(event_type=ControlPlaneEventType.INTENT_RECEIVED))
        trail.append(ControlPlaneEvent(event_type=ControlPlaneEventType.ERROR_OCCURRED))
        events = trail.get_events_by_type(ControlPlaneEventType.INTENT_RECEIVED)
        assert len(events) == 2

    def test_len(self):
        trail = AuditTrail()
        trail.append(ControlPlaneEvent())
        trail.append(ControlPlaneEvent())
        assert len(trail) == 2


class TestControlPlaneObserver:
    def test_observe_event_returns_event(self):
        obs = ControlPlaneObserver()
        event = obs.observe_event(ControlPlaneEventType.INTENT_RECEIVED, intent_id="o1")
        assert isinstance(event, ControlPlaneEvent)
        assert event.intent_id == "o1"

    def test_metrics_increment_intents(self):
        obs = ControlPlaneObserver()
        obs.observe_event(ControlPlaneEventType.INTENT_RECEIVED)
        summary = obs.get_metrics_summary()
        assert summary["total_intents"] == 1

    def test_metrics_track_compilations(self):
        obs = ControlPlaneObserver()
        obs.observe_event(ControlPlaneEventType.INTENT_COMPILED, duration_ms=5.0)
        summary = obs.get_metrics_summary()
        assert summary["total_compilations"] == 1
        assert summary["avg_compilation_latency_ms"] == 5.0

    def test_register_handler_called(self):
        obs = ControlPlaneObserver()
        captured = []
        obs.register_handler(lambda e: captured.append(e))
        obs.observe_event(ControlPlaneEventType.INTENT_RECEIVED)
        assert len(captured) == 1

    def test_unregister_handler(self):
        obs = ControlPlaneObserver()
        captured = []

        def handler(e):
            captured.append(e)

        obs.register_handler(handler)
        obs.unregister_handler(handler)
        obs.observe_event(ControlPlaneEventType.INTENT_RECEIVED)
        assert len(captured) == 0

    def test_get_intent_timeline(self):
        obs = ControlPlaneObserver()
        obs.observe_event(ControlPlaneEventType.INTENT_RECEIVED, intent_id="t1")
        obs.observe_event(ControlPlaneEventType.INTENT_COMPILED, intent_id="t1")
        obs.observe_event(ControlPlaneEventType.INTENT_RECEIVED, intent_id="t2")
        timeline = obs.get_intent_timeline("t1")
        assert len(timeline) == 2

    def test_verify_audit_integrity(self):
        obs = ControlPlaneObserver()
        obs.observe_event(ControlPlaneEventType.INTENT_RECEIVED)
        obs.observe_event(ControlPlaneEventType.INTENT_COMPILED)
        assert obs.verify_audit_integrity() is True

    def test_reset_metrics(self):
        obs = ControlPlaneObserver()
        obs.observe_event(ControlPlaneEventType.INTENT_RECEIVED)
        obs.reset_metrics()
        summary = obs.get_metrics_summary()
        assert summary["total_intents"] == 0

    def test_failure_metrics(self):
        obs = ControlPlaneObserver()
        obs.observe_event(ControlPlaneEventType.GRAPH_FAILED)
        obs.observe_event(ControlPlaneEventType.ERROR_OCCURRED)
        summary = obs.get_metrics_summary()
        assert summary["total_failures"] == 2

    def test_event_to_dict(self):
        event = ControlPlaneEvent(
            event_type=ControlPlaneEventType.NODE_COMPLETED,
            intent_id="d1",
            node_id="n1",
        )
        d = event.to_dict()
        assert d["event_type"] == "node_completed"
        assert d["node_id"] == "n1"


# ===================================================================
# C-5: Signed Execution
# ===================================================================


class TestSignedExecution:
    def setup_method(self):
        self.private_key, self.public_key = generate_keypair()

    def test_generate_keypair_lengths(self):
        assert len(self.private_key) == 32
        assert len(self.public_key) == 32

    def test_sign_produces_hex_string(self):
        pkt = JITNAPacketCP(source_agent_id="a", target_agent_id="b", payload={"x": 1})
        sig = sign_packet(pkt, self.private_key)
        assert isinstance(sig, str)
        assert len(sig) == 128  # ED25519 sig = 64 bytes → 128 hex chars

    def test_verify_valid_signature(self):
        pkt = JITNAPacketCP(source_agent_id="a", target_agent_id="b", payload={"x": 1})
        sig = sign_packet(pkt, self.private_key)
        assert verify_packet(pkt, sig, self.public_key) is True

    def test_verify_wrong_key_fails(self):
        pkt = JITNAPacketCP(source_agent_id="a", target_agent_id="b", payload={"x": 1})
        sig = sign_packet(pkt, self.private_key)
        _, other_pub = generate_keypair()
        assert verify_packet(pkt, sig, other_pub) is False

    def test_verify_tampered_payload_fails(self):
        pkt = JITNAPacketCP(source_agent_id="a", target_agent_id="b", payload={"x": 1})
        sig = sign_packet(pkt, self.private_key)
        pkt.payload["x"] = 999
        assert verify_packet(pkt, sig, self.public_key) is False

    def test_key_fingerprint_deterministic(self):
        fp1 = compute_key_fingerprint(self.public_key)
        fp2 = compute_key_fingerprint(self.public_key)
        assert fp1 == fp2
        assert len(fp1) == 64

    def test_signed_execution_packet_sign_and_verify(self):
        pkt = JITNAPacketCP(source_agent_id="a", target_agent_id="b", payload={"cmd": "deploy"})
        signed = SignedExecutionPacket.sign(pkt, self.private_key, self.public_key)
        assert signed.signature != ""
        assert signed.public_key_fingerprint != ""
        assert signed.verify(self.public_key) is True

    def test_signed_packet_to_dict(self):
        pkt = JITNAPacketCP(source_agent_id="a", target_agent_id="b")
        signed = SignedExecutionPacket.sign(pkt, self.private_key, self.public_key)
        d = signed.to_dict()
        assert "signature" in d
        assert "packet" in d


# ===================================================================
# D-1: Middleware — FeatureFlagStore
# ===================================================================


class TestFeatureFlagStore:
    def _fresh_store(self) -> FeatureFlagStore:
        return FeatureFlagStore()

    def test_default_flags_seeded(self):
        store = self._fresh_store()
        flags = store.get_all()
        assert "enable_marketplace" in flags
        assert "enable_status_page" in flags

    def test_status_page_enabled_by_default(self):
        store = self._fresh_store()
        assert store.is_enabled("enable_status_page") is True

    def test_marketplace_disabled_by_default(self):
        store = self._fresh_store()
        assert store.is_enabled("enable_marketplace") is False

    def test_nonexistent_flag_returns_false(self):
        store = self._fresh_store()
        assert store.is_enabled("does_not_exist") is False

    def test_set_flag(self):
        store = self._fresh_store()
        store.set_flag("enable_marketplace", True)
        store.set_rollout("enable_marketplace", 100)
        # After enabling + 100% rollout, check with environment match
        assert store.is_enabled("enable_marketplace", user_id="u1", environment="production") is True

    def test_toggle_flag(self):
        store = self._fresh_store()
        original = store.get_flag("enable_marketplace").enabled
        result = store.toggle_flag("enable_marketplace")
        assert result == (not original)

    def test_blacklist_blocks_whitelisted_user(self):
        store = self._fresh_store()
        store.set_flag("enable_marketplace", True)
        store.add_to_whitelist("enable_marketplace", "user-1")
        store.add_to_blacklist("enable_marketplace", "user-1")
        # Blacklist wins over whitelist
        assert store.is_enabled("enable_marketplace", user_id="user-1", environment="production") is False

    def test_whitelist_bypasses_disabled_flag(self):
        store = self._fresh_store()
        # enable_marketplace is disabled by default
        store.add_to_whitelist("enable_marketplace", "vip-user")
        assert store.is_enabled("enable_marketplace", user_id="vip-user") is True

    def test_rollout_percentage(self):
        store = self._fresh_store()
        store.set_flag("enable_marketplace", True)
        store.set_rollout("enable_marketplace", 100)
        assert store.is_enabled("enable_marketplace", user_id="any-user", environment="production") is True

    def test_set_rollout_invalid_raises(self):
        store = self._fresh_store()
        with pytest.raises(ValueError):
            store.set_rollout("enable_marketplace", 200)

    def test_create_flag(self):
        store = self._fresh_store()
        new_flag = FlagDefinition(
            flag_key="test_new_flag",
            description="Test",
            enabled=True,
            rollout_percentage=100,
            environments=["*"],
        )
        assert store.create_flag(new_flag) is True
        assert store.is_enabled("test_new_flag", user_id="any") is True

    def test_create_duplicate_returns_false(self):
        store = self._fresh_store()
        dup = FlagDefinition(flag_key="enable_marketplace", description="dup", enabled=True)
        assert store.create_flag(dup) is False

    def test_remove_user_override(self):
        store = self._fresh_store()
        store.add_to_whitelist("enable_marketplace", "u1")
        store.remove_user_override("enable_marketplace", "u1")
        flag = store.get_flag("enable_marketplace")
        assert "u1" not in flag.user_whitelist

    def test_list_flags_returns_dicts(self):
        store = self._fresh_store()
        flags = store.list_flags()
        assert isinstance(flags, list)
        assert all("flag_key" in f for f in flags)


# ===================================================================
# D-2: Default Policies
# ===================================================================


class TestDefaultPolicies:
    def test_get_default_policies_returns_eight(self):
        policies = get_default_policies()
        assert len(policies) == 8
        assert all(isinstance(p, PolicyRule) for p in policies)

    def test_cost_cap_rejects_high_cost(self):
        rule = create_cost_cap_policy(max_cost_usd=Decimal("100"))
        assert rule.action == PolicyAction.REJECT
        assert rule.evaluate({"estimated_cost_usd": Decimal("200")}) is True
        assert rule.evaluate({"estimated_cost_usd": Decimal("50")}) is False

    def test_risk_escalation_triggers_on_systemic(self):
        from rct_control_plane.intent_schema import RiskProfile
        rule = create_risk_escalation_policy()
        assert rule.action == PolicyAction.ESCALATE
        assert rule.evaluate({"risk_profile": RiskProfile.SYSTEMIC}) is True
        assert rule.evaluate({"risk_profile": RiskProfile.LOW}) is False

    def test_time_limit_triggers_on_long_duration(self):
        rule = create_time_limit_policy(max_hours=2)
        assert rule.action == PolicyAction.REQUIRE_APPROVAL
        assert rule.evaluate({"estimated_duration_seconds": 7200}) is True
        assert rule.evaluate({"estimated_duration_seconds": 3600}) is False

    def test_certification_gate_for_deploy(self):
        from rct_control_plane.intent_schema import IntentType
        rule = create_certification_gate_policy()
        assert rule.action == PolicyAction.REQUIRE_APPROVAL
        assert rule.evaluate({"intent_type": IntentType.DEPLOY}) is True
        assert rule.evaluate({"intent_type": IntentType.REFACTOR}) is False

    def test_compliance_check_rejects_free_deploy(self):
        from rct_control_plane.intent_schema import IntentType
        rule = create_compliance_check_policy()
        assert rule.action == PolicyAction.REJECT
        assert rule.evaluate({"user_tier": "FREE", "intent_type": IntentType.DEPLOY}) is True
        assert rule.evaluate({"user_tier": "PRO", "intent_type": IntentType.DEPLOY}) is False

    def test_data_sensitivity_logs_broad_scope(self):
        rule = create_data_sensitivity_policy()
        assert rule.action == PolicyAction.LOG
        assert rule.evaluate({"scope_type": "SYSTEM"}) is True
        assert rule.evaluate({"scope_type": "FILE"}) is False

    def test_approval_workflow_cost_threshold(self):
        rule = create_approval_workflow_policy(cost_threshold=Decimal("50"))
        assert rule.evaluate({"estimated_cost_usd": Decimal("75")}) is True
        assert rule.evaluate({"estimated_cost_usd": Decimal("25")}) is False

    def test_resource_quota_notifies(self):
        rule = create_resource_quota_policy(max_memory_gb=16.0, max_cpu_cores=8)
        assert rule.action == PolicyAction.NOTIFY

    def test_create_custom_policy(self):
        from rct_control_plane.policy_language import ConditionOperator, PolicyCondition
        rule = create_custom_policy(
            name="Custom",
            description="Block large graphs",
            conditions=[PolicyCondition(field="node_count", operator=ConditionOperator.GREATER_THAN, value=100)],
            action=PolicyAction.REJECT,
        )
        assert rule.name == "Custom"
        assert rule.evaluate({"node_count": 200}) is True


# ===================================================================
# D-3: Benchmark CLI (import + structure)
# ===================================================================


class TestBenchmarkCLI:
    def test_import_module(self):
        from benchmark import run_benchmark
        assert hasattr(run_benchmark, "main")
        assert hasattr(run_benchmark, "SUITES")

    def test_suites_dict_has_expected_keys(self):
        from benchmark.run_benchmark import SUITES
        assert "fdia_scoring" in SUITES
        assert "intent_compile" in SUITES
        assert "signedai_routing" in SUITES

    def test_benchmark_result_dataclass(self):
        from benchmark.run_benchmark import BenchmarkResult
        r = BenchmarkResult(suite="test", iterations=10, avg_ms=1.5)
        d = r.to_dict()
        assert d["suite"] == "test"

    def test_run_iterations_helper(self):
        from benchmark.run_benchmark import _run_iterations
        result = _run_iterations("noop", lambda: None, 10)
        assert result.iterations == 10
        assert result.errors == 0
        assert result.avg_ms >= 0

    def test_vector_engine_suite_runs(self):
        from benchmark.run_benchmark import bench_vector_engine
        result = bench_vector_engine(n=5)
        assert result.iterations == 5
        assert result.errors == 0
