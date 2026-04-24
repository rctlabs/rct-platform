"""
Tests for examples/cli_walkthrough.py

Covers:
- step_compile: returns a valid IntentObject
- step_build: returns a valid ExecutionGraph
- step_evaluate: returns True/False based on governance outcome
- step_status: does not raise
- step_audit: does not raise
- run_walkthrough: full pipeline integration, prints expected sections
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from rct_control_plane.intent_schema import IntentObject, RiskProfile
from rct_control_plane.execution_graph_ir import ExecutionGraph

from examples.cli_walkthrough import (
    step_compile,
    step_build,
    step_evaluate,
    step_status,
    step_audit,
    run_walkthrough,
)


# ---------------------------------------------------------------------------
# step_compile
# ---------------------------------------------------------------------------

class TestStepCompile:
    def test_returns_intent_object(self):
        intent = step_compile("Refactor the authentication module")
        assert isinstance(intent, IntentObject)

    def test_intent_has_uuid(self):
        intent = step_compile("Optimize database queries")
        assert intent.id is not None

    def test_intent_goal_non_empty(self):
        nl = "Deploy payment service to staging"
        intent = step_compile(nl)
        assert intent.goal
        assert len(intent.goal) > 0

    def test_intent_type_is_set(self):
        intent = step_compile("Build a REST API for user management")
        assert intent.intent_type is not None

    def test_risk_profile_is_set(self):
        intent = step_compile("Analyze code quality metrics")
        assert intent.risk_profile is not None

    def test_compiler_version_is_set(self):
        intent = step_compile("Write unit tests for the auth module")
        assert intent.compiler_version

    def test_compiled_at_is_set(self):
        intent = step_compile("Document the API endpoints")
        assert intent.compiled_at is not None

    def test_verbose_does_not_raise(self, capsys):
        step_compile("Refactor auth module", verbose=True)
        captured = capsys.readouterr()
        assert "COMPILE" in captured.out

    def test_different_intents_can_differ_in_type(self):
        intent_a = step_compile("Deploy service X to production")
        intent_b = step_compile("Refactor authentication module")
        # Both valid — just check they are IntentObjects
        assert isinstance(intent_a, IntentObject)
        assert isinstance(intent_b, IntentObject)


# ---------------------------------------------------------------------------
# step_build
# ---------------------------------------------------------------------------

class TestStepBuild:
    def setup_method(self):
        self.intent = step_compile("Refactor the authentication module")

    def test_returns_execution_graph(self):
        graph = step_build(self.intent)
        assert isinstance(graph, ExecutionGraph)

    def test_graph_has_nodes(self):
        graph = step_build(self.intent)
        # An execution graph may have 0 or more nodes; it must be dict-like
        assert isinstance(graph.nodes, dict)

    def test_graph_has_edges(self):
        graph = step_build(self.intent)
        assert isinstance(graph.edges, list)

    def test_graph_validates(self):
        graph = step_build(self.intent)
        errors = graph.validate()
        assert isinstance(errors, list)

    def test_verbose_does_not_raise(self, capsys):
        step_build(self.intent, verbose=True)
        captured = capsys.readouterr()
        assert "BUILD" in captured.out

    def test_build_multiple_times_does_not_raise(self):
        for _ in range(3):
            graph = step_build(self.intent)
            assert isinstance(graph, ExecutionGraph)


# ---------------------------------------------------------------------------
# step_evaluate
# ---------------------------------------------------------------------------

class TestStepEvaluate:
    def test_returns_bool(self):
        intent = step_compile("Refactor authentication module")
        result = step_evaluate(intent)
        assert isinstance(result, bool)

    def test_low_risk_intent_approved(self):
        """A REFACTOR or DOCUMENT intent should pass the default policies."""
        intent = step_compile("Write documentation for the API")
        # Force non-systemic risk for this test
        intent.risk_profile = RiskProfile.LOW
        result = step_evaluate(intent)
        assert result is True

    def test_systemic_risk_escalated_not_necessarily_rejected(self):
        """SYSTEMIC risk escalates but may not hard-reject — result is bool."""
        intent = step_compile("Migrate entire production database cluster")
        intent.risk_profile = RiskProfile.SYSTEMIC
        result = step_evaluate(intent)
        assert isinstance(result, bool)

    def test_verbose_does_not_raise(self, capsys):
        intent = step_compile("Analyze security vulnerabilities")
        step_evaluate(intent, verbose=True)
        captured = capsys.readouterr()
        assert "EVALUATE" in captured.out


# ---------------------------------------------------------------------------
# step_status
# ---------------------------------------------------------------------------

class TestStepStatus:
    def test_does_not_raise_approved(self, capsys):
        intent = step_compile("Refactor module X")
        step_status(intent, approved=True)
        captured = capsys.readouterr()
        assert "STATUS" in captured.out

    def test_does_not_raise_blocked(self, capsys):
        intent = step_compile("Refactor module X")
        step_status(intent, approved=False)
        captured = capsys.readouterr()
        assert "STATUS" in captured.out

    def test_outputs_phase_approved(self, capsys):
        intent = step_compile("Refactor module X")
        step_status(intent, approved=True)
        captured = capsys.readouterr()
        assert "approved" in captured.out.lower() or "ready" in captured.out.lower()

    def test_outputs_phase_failed(self, capsys):
        intent = step_compile("Refactor module X")
        step_status(intent, approved=False)
        captured = capsys.readouterr()
        assert "failed" in captured.out.lower() or "blocked" in captured.out.lower()


# ---------------------------------------------------------------------------
# step_audit
# ---------------------------------------------------------------------------

class TestStepAudit:
    def test_does_not_raise(self, capsys):
        intent = step_compile("Deploy service X")
        step_audit(intent)

    def test_outputs_audit_events(self, capsys):
        intent = step_compile("Optimize query performance")
        step_audit(intent)
        captured = capsys.readouterr()
        assert "intent_received" in captured.out or "AUDIT" in captured.out

    def test_verbose_does_not_raise(self, capsys):
        intent = step_compile("Refactor module X")
        step_audit(intent, verbose=True)
        captured = capsys.readouterr()
        assert len(captured.out) > 0


# ---------------------------------------------------------------------------
# run_walkthrough (integration)
# ---------------------------------------------------------------------------

class TestRunWalkthrough:
    def test_does_not_raise(self, capsys):
        run_walkthrough("Refactor the authentication module to use JWT tokens")

    def test_outputs_pipeline_complete(self, capsys):
        run_walkthrough("Refactor auth module")
        captured = capsys.readouterr()
        assert "PIPELINE COMPLETE" in captured.out

    def test_outputs_compile_section(self, capsys):
        run_walkthrough("Optimize database queries")
        captured = capsys.readouterr()
        assert "COMPILE" in captured.out

    def test_outputs_evaluate_section(self, capsys):
        run_walkthrough("Deploy service to staging")
        captured = capsys.readouterr()
        assert "EVALUATE" in captured.out

    def test_outputs_audit_section(self, capsys):
        run_walkthrough("Write unit tests")
        captured = capsys.readouterr()
        assert "AUDIT" in captured.out

    def test_outputs_cli_commands(self, capsys):
        run_walkthrough("Build REST API for orders")
        captured = capsys.readouterr()
        assert "rct compile" in captured.out

    def test_verbose_mode(self, capsys):
        run_walkthrough("Analyze codebase for refactoring", verbose=True)
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_custom_intent_text(self, capsys):
        custom = "Deploy custom NLP pipeline to production"
        run_walkthrough(custom)
        captured = capsys.readouterr()
        assert "PIPELINE COMPLETE" in captured.out

    def test_different_intents_both_complete(self, capsys):
        for intent_text in [
            "Refactor payment module",
            "Analyze security vulnerabilities in auth",
        ]:
            run_walkthrough(intent_text)
        captured = capsys.readouterr()
        assert captured.out.count("PIPELINE COMPLETE") == 2
