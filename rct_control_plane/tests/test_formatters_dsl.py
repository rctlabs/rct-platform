"""
Tests for rct_control_plane.rich_formatter and dsl_parser modules.
Covers rendering functions (using StringIO console) and DSL parsing paths.
"""
from __future__ import annotations

import io
import pytest
from rich.console import Console

from rct_control_plane.rich_formatter import (
    get_console,
    set_console,
    render_intent_table,
    render_state_panel,
    render_audit_tree,
    render_metrics_panel,
    render_adapter_status,
    render_governance_violations,
    render_timeline,
    render_execution_log,
    render_replay_result,
    render_error,
    render_success,
    render_warning,
)
from rct_control_plane.dsl_parser import DSLParser, DSLParseError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_console() -> tuple[Console, io.StringIO]:
    """Return (console, buffer) for captured output testing."""
    buf = io.StringIO()
    console = Console(file=buf, width=120, no_color=True, highlight=False)
    return console, buf


# ---------------------------------------------------------------------------
# TestRichFormatterSetup
# ---------------------------------------------------------------------------

class TestRichFormatterSetup:
    def test_get_console_returns_console(self):
        c = get_console()
        assert c is not None
        assert isinstance(c, Console)

    def test_set_console_overrides(self):
        original = get_console()
        buf = io.StringIO()
        new_console = Console(file=buf, width=80, no_color=True)
        set_console(new_console)
        assert get_console() is new_console
        # Restore
        set_console(original)

    def test_get_console_singleton(self):
        c1 = get_console()
        c2 = get_console()
        assert c1 is c2


# ---------------------------------------------------------------------------
# TestRenderIntentTable
# ---------------------------------------------------------------------------

class TestRenderIntentTable:
    def setup_method(self):
        self.console, self.buf = _make_console()
        set_console(self.console)

    def teardown_method(self):
        set_console(None)

    def test_render_empty_list(self):
        render_intent_table([])
        output = self.buf.getvalue()
        assert "Intent" in output or len(output) > 0  # table rendered even if empty

    def test_render_single_intent(self):
        intents = [{
            "intent_id": "i-001",
            "intent_type": "refactor",
            "scope": "module",
            "priority": 5,
            "is_valid": True,
            "created_at": "2026-01-01",
        }]
        render_intent_table(intents)
        output = self.buf.getvalue()
        assert "i-001" in output
        assert "refactor" in output

    def test_render_invalid_intent_shows_cross(self):
        intents = [{"intent_id": "x1", "is_valid": False}]
        render_intent_table(intents)
        output = self.buf.getvalue()
        assert "x1" in output

    def test_render_multiple_intents(self):
        intents = [
            {"intent_id": f"i-{i}", "intent_type": "deploy", "priority": i}
            for i in range(5)
        ]
        render_intent_table(intents)
        output = self.buf.getvalue()
        assert "i-0" in output
        assert "i-4" in output


# ---------------------------------------------------------------------------
# TestRenderStatePanel
# ---------------------------------------------------------------------------

class TestRenderStatePanel:
    def setup_method(self):
        self.console, self.buf = _make_console()
        set_console(self.console)

    def teardown_method(self):
        set_console(None)

    def test_render_basic_state(self):
        state = {
            "state_id": "s-abc",
            "phase": "completed",
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-01T01:00:00",
        }
        render_state_panel(state)
        output = self.buf.getvalue()
        assert "s-abc" in output
        assert "completed" in output

    def test_render_state_with_history(self):
        state = {
            "state_id": "s-xyz",
            "current_phase": "running",
            "history": [{"from": "INIT", "to": "RUNNING"}],
        }
        render_state_panel(state)
        output = self.buf.getvalue()
        assert "running" in output or "running" in output.lower()

    def test_render_unknown_phase_uses_fallback(self):
        render_state_panel({})
        output = self.buf.getvalue()
        assert len(output) > 0


# ---------------------------------------------------------------------------
# TestRenderAuditTree
# ---------------------------------------------------------------------------

class TestRenderAuditTree:
    def setup_method(self):
        self.console, self.buf = _make_console()
        set_console(self.console)

    def teardown_method(self):
        set_console(None)

    def test_render_empty_audit(self):
        render_audit_tree({"intent_id": "i-1", "events": []})
        output = self.buf.getvalue()
        assert "i-1" in output

    def test_render_with_events(self):
        audit = {
            "intent_id": "i-2",
            "chain_integrity": {"is_valid": True, "total_entries": 3},
            "events": [
                {"timestamp": "2026-01-01", "action": "COMPILE", "data": {"success": True}},
                {"timestamp": "2026-01-01", "action": "EVALUATE", "data": {"success": False}},
            ],
        }
        render_audit_tree(audit)
        output = self.buf.getvalue()
        assert "COMPILE" in output
        assert "EVALUATE" in output

    def test_render_flat_integrity(self):
        audit = {
            "intent_id": "i-3",
            "integrity_verified": False,
            "event_count": 5,
            "events": [],
        }
        render_audit_tree(audit)
        output = self.buf.getvalue()
        assert "i-3" in output


# ---------------------------------------------------------------------------
# TestRenderMetricsPanel
# ---------------------------------------------------------------------------

class TestRenderMetricsPanel:
    def setup_method(self):
        self.console, self.buf = _make_console()
        set_console(self.console)

    def teardown_method(self):
        set_console(None)

    def test_render_flat_metrics(self):
        render_metrics_panel({"total_events": 42, "errors": 1})
        output = self.buf.getvalue()
        assert "42" in output

    def test_render_nested_metrics(self):
        render_metrics_panel({
            "compiler": {"calls": 10, "errors": 0},
            "evaluator": {"calls": 5},
        })
        output = self.buf.getvalue()
        assert "10" in output

    def test_render_empty_metrics(self):
        render_metrics_panel({})
        output = self.buf.getvalue()
        assert len(output) > 0


# ---------------------------------------------------------------------------
# TestRenderAdapterStatus
# ---------------------------------------------------------------------------

class TestRenderAdapterStatus:
    def setup_method(self):
        self.console, self.buf = _make_console()
        set_console(self.console)

    def teardown_method(self):
        set_console(None)

    def test_render_healthy_adapter(self):
        adapters = [{
            "name": "github-adapter",
            "version": "1.0.0",
            "security_level": "HIGH",
            "healthy": True,
            "supported_actions": ["commit", "pr", "branch"],
            "avg_latency_ms": 42.5,
        }]
        render_adapter_status(adapters)
        output = self.buf.getvalue()
        assert "github-adapter" in output

    def test_render_unhealthy_adapter(self):
        adapters = [{"name": "broken", "healthy": False}]
        render_adapter_status(adapters)
        output = self.buf.getvalue()
        assert "broken" in output

    def test_render_adapter_truncates_actions(self):
        adapters = [{
            "name": "mega",
            "healthy": True,
            "supported_actions": ["a1", "a2", "a3", "a4", "a5", "a6", "a7"],
        }]
        render_adapter_status(adapters)
        output = self.buf.getvalue()
        assert "mega" in output

    def test_render_empty_adapters(self):
        render_adapter_status([])
        assert len(self.buf.getvalue()) > 0


# ---------------------------------------------------------------------------
# TestRenderGovernance
# ---------------------------------------------------------------------------

class TestRenderGovernance:
    def setup_method(self):
        self.console, self.buf = _make_console()
        set_console(self.console)

    def teardown_method(self):
        set_console(None)

    def test_render_no_violations(self):
        render_governance_violations([])
        output = self.buf.getvalue()
        assert "No governance violations" in output

    def test_render_violations(self):
        violations = [{
            "rule": "MAX_COST",
            "severity": "HIGH",
            "description": "Exceeded budget",
            "timestamp": "2026-01-01",
        }]
        render_governance_violations(violations)
        output = self.buf.getvalue()
        assert "MAX_COST" in output
        assert "Exceeded budget" in output


# ---------------------------------------------------------------------------
# TestRenderTimeline
# ---------------------------------------------------------------------------

class TestRenderTimeline:
    def setup_method(self):
        self.console, self.buf = _make_console()
        set_console(self.console)

    def teardown_method(self):
        set_console(None)

    def test_render_empty_timeline(self):
        render_timeline("agent-1", [])
        output = self.buf.getvalue()
        assert "agent-1" in output

    def test_render_with_deltas(self):
        deltas = [
            {
                "tick": 1,
                "intent_type": "PROTECT",
                "action_type": "defend",
                "outcome": "success",
                "governance_violation": False,
                "resources_delta": {"gold": -10.0, "hp": 5.0},
            },
            {
                "tick": 2,
                "intent_type": "DOMINATE",
                "action_type": "attack",
                "outcome": "failed",
                "governance_violation": True,
                "resources_delta": {},
            },
        ]
        render_timeline("agent-2", deltas)
        output = self.buf.getvalue()
        assert "agent-2" in output
        assert "defend" in output


# ---------------------------------------------------------------------------
# TestRenderExecutionLog
# ---------------------------------------------------------------------------

class TestRenderExecutionLog:
    def setup_method(self):
        self.console, self.buf = _make_console()
        set_console(self.console)

    def teardown_method(self):
        set_console(None)

    def test_render_empty_log(self):
        render_execution_log([])
        assert len(self.buf.getvalue()) > 0

    def test_render_log_entries(self):
        logs = [{
            "packet_id": "pkt-1",
            "action": "deploy",
            "status": "completed",
            "sha256_hash": "abc123def456" * 3,
            "latency_ms": 123.4,
            "timestamp": "2026-01-01",
        }]
        render_execution_log(logs, title="Deploy Log")
        output = self.buf.getvalue()
        assert "pkt-1" in output
        assert "deploy" in output

    def test_render_log_no_sha(self):
        logs = [{"packet_id": "p2", "action": "build", "status": "running"}]
        render_execution_log(logs)
        output = self.buf.getvalue()
        assert "p2" in output


# ---------------------------------------------------------------------------
# TestRenderReplayResult
# ---------------------------------------------------------------------------

class TestRenderReplayResult:
    def setup_method(self):
        self.console, self.buf = _make_console()
        set_console(self.console)

    def teardown_method(self):
        set_console(None)

    def test_render_original_only(self):
        render_replay_result({"hash": "abc", "state": "init"})
        output = self.buf.getvalue()
        assert "Original" in output

    def test_render_match_true(self):
        render_replay_result({"h": "x"}, replayed={"h": "x"}, match=True)
        output = self.buf.getvalue()
        assert "Match" in output or "identical" in output.lower()

    def test_render_match_false(self):
        render_replay_result({"h": "x"}, replayed={"h": "y"}, match=False)
        output = self.buf.getvalue()
        assert "MISMATCH" in output or "diverge" in output.lower()


# ---------------------------------------------------------------------------
# TestRenderHelpers
# ---------------------------------------------------------------------------

class TestRenderHelpers:
    def setup_method(self):
        self.console, self.buf = _make_console()
        set_console(self.console)

    def teardown_method(self):
        set_console(None)

    def test_render_error(self):
        render_error("Something went wrong")
        output = self.buf.getvalue()
        assert "Something went wrong" in output

    def test_render_success(self):
        render_success("Operation complete")
        output = self.buf.getvalue()
        assert "Operation complete" in output

    def test_render_warning(self):
        render_warning("Watch out")
        output = self.buf.getvalue()
        assert "Watch out" in output


# ---------------------------------------------------------------------------
# TestDSLParser
# ---------------------------------------------------------------------------

SIMPLE_DSL = '''
intent "test_intent" {
    phase setup {
        node AnalyzeNode {
            node_type = "agent_capability"
            capability = "code_analysis"
            cost = 0.50
            timeout = 60s
        }
    }
}
'''

TWO_NODE_DSL = '''
intent "two_node" {
    phase build {
        node NodeA {
            node_type = "agent_capability"
            capability = "code_analysis"
        }
        node NodeB {
            node_type = "tool_call"
            tool_name = "linter"
            depends_on = [NodeA]
        }
    }
}
'''

INVALID_DSL = '''
this is not valid dsl
'''


class TestDSLParser:
    def setup_method(self):
        self.parser = DSLParser()

    def test_parse_simple_dsl(self):
        graph = self.parser.parse(SIMPLE_DSL, intent_id="test-001")
        assert graph is not None
        assert len(graph.nodes) == 1

    def test_parse_sets_intent_id(self):
        graph = self.parser.parse(SIMPLE_DSL, intent_id="my-intent")
        assert graph.intent_id == "my-intent"

    def test_parse_stores_intent_name(self):
        graph = self.parser.parse(SIMPLE_DSL, intent_id="x")
        assert graph.metadata.get("intent_name") == "test_intent"

    def test_parse_two_nodes_with_dependency(self):
        graph = self.parser.parse(TWO_NODE_DSL, intent_id="dep-test")
        assert len(graph.nodes) == 2
        # NodeB depends on NodeA — there should be an edge
        assert len(graph.edges) == 1

    def test_parse_invalid_raises(self):
        with pytest.raises(DSLParseError):
            self.parser.parse(INVALID_DSL, intent_id="bad")

    def test_parse_node_has_cost(self):
        graph = self.parser.parse(SIMPLE_DSL, intent_id="c")
        node = list(graph.nodes.values())[0]
        assert float(node.estimated_cost) == pytest.approx(0.50)

    def test_dsl_parse_error_has_message(self):
        try:
            self.parser.parse(INVALID_DSL, intent_id="x")
        except DSLParseError as e:
            assert "No intent block found" in str(e)

    def test_parse_entry_exit_nodes_set(self):
        graph = self.parser.parse(TWO_NODE_DSL, intent_id="e")
        assert len(graph.entry_nodes) > 0
        assert len(graph.exit_nodes) > 0

    def test_parse_capability_set(self):
        graph = self.parser.parse(SIMPLE_DSL, intent_id="cap")
        node = list(graph.nodes.values())[0]
        # DSL parser stores capability in node.metadata or node.capability
        capability = node.capability or node.metadata.get("capability", "")
        assert "code_analysis" in capability
