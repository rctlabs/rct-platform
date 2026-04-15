"""
Tests for rct_control_plane — execution_graph_ir, dsl_parser, intent_schema,
control_plane_state. All public API surfaces with no external I/O dependencies.
"""

import pytest
from decimal import Decimal
from uuid import uuid4

# ---------------------------------------------------------------------------
# execution_graph_ir
# ---------------------------------------------------------------------------
from rct_control_plane.execution_graph_ir import (
    DependencyEdge,
    DependencyType,
    ExecutionGraph,
    ExecutionNode,
    NodeStatus,
    NodeType,
    ResourceRequirement,
)


class TestExecutionGraph:
    def test_create_empty_graph(self):
        graph = ExecutionGraph(intent_id="test-001")
        assert graph.intent_id == "test-001"
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_add_node(self):
        graph = ExecutionGraph(intent_id="test-002")
        node = ExecutionNode(
            id="node_a",
            node_type=NodeType.AGENT_CAPABILITY,
            capability="code_analysis",
        )
        graph.add_node(node)
        assert "node_a" in graph.nodes
        assert graph.nodes["node_a"].capability == "code_analysis"

    def test_duplicate_node_raises(self):
        graph = ExecutionGraph(intent_id="test-003")
        node = ExecutionNode(id="node_a", node_type=NodeType.TOOL_CALL)
        graph.add_node(node)
        with pytest.raises(ValueError, match="already exists"):
            graph.add_node(node)

    def test_add_edge(self):
        graph = ExecutionGraph(intent_id="test-004")
        n1 = ExecutionNode(id="a", node_type=NodeType.AGENT_CAPABILITY, capability="read")
        n2 = ExecutionNode(id="b", node_type=NodeType.AGENT_CAPABILITY, capability="write")
        graph.add_node(n1)
        graph.add_node(n2)
        edge = DependencyEdge(from_node="a", to_node="b", dependency_type=DependencyType.SEQUENTIAL)
        graph.add_edge(edge)
        assert len(graph.edges) == 1

    def test_cycle_detection(self):
        graph = ExecutionGraph(intent_id="test-cycle")
        n1 = ExecutionNode(id="a", node_type=NodeType.AGENT_CAPABILITY)
        n2 = ExecutionNode(id="b", node_type=NodeType.AGENT_CAPABILITY)
        graph.add_node(n1)
        graph.add_node(n2)
        graph.add_edge(DependencyEdge(from_node="a", to_node="b"))
        with pytest.raises(ValueError, match="[Cc]ycle"):
            graph.add_edge(DependencyEdge(from_node="b", to_node="a"))

    def test_validate_empty_graph_ok(self):
        graph = ExecutionGraph(intent_id="empty")
        errors = graph.validate()
        assert errors == []

    def test_graph_id_is_auto_generated(self):
        g1 = ExecutionGraph(intent_id="x")
        g2 = ExecutionGraph(intent_id="x")
        assert g1.graph_id != g2.graph_id

    def test_node_status_default_pending(self):
        node = ExecutionNode(id="n", node_type=NodeType.CHECKPOINT)
        assert node.status == NodeStatus.PENDING

    def test_node_estimated_cost_default_zero(self):
        node = ExecutionNode(id="n", node_type=NodeType.TOOL_CALL)
        assert node.estimated_cost == Decimal("0.0")

    def test_node_type_tool_call(self):
        node = ExecutionNode(id="t", node_type=NodeType.TOOL_CALL, tool_name="grep_tool")
        assert node.node_type == NodeType.TOOL_CALL
        assert node.tool_name == "grep_tool"

    def test_resource_requirement_defaults(self):
        res = ResourceRequirement()
        assert res.max_cost_usd is None
        assert res.requires_gpu is False


# ---------------------------------------------------------------------------
# dsl_parser
# ---------------------------------------------------------------------------
from rct_control_plane.dsl_parser import DSLParser, DSLParseError


class TestDSLParser:
    DSL_SIMPLE = '''\
intent "test_intent" {
    phase analyze {
        node AnalyzeNode {
            agent_capability = "code_analysis"
            cost = 0.50
            timeout = 60s
        }
    }
}
'''

    DSL_TWO_PHASES = '''\
intent "multi_phase" {
    phase analyze {
        node Analyze {
            agent_capability = "analysis"
            cost = 0.25
        }
    }
    phase implement {
        node Implement {
            agent_capability = "code_write"
            cost = 0.75
            depends_on = [Analyze]
        }
    }
}
'''

    def test_parse_simple_dsl(self):
        parser = DSLParser()
        graph = parser.parse(self.DSL_SIMPLE, intent_id="abc")
        assert len(graph.nodes) == 1
        assert "AnalyzeNode" in graph.nodes

    def test_parse_sets_intent_id(self):
        parser = DSLParser()
        graph = parser.parse(self.DSL_SIMPLE, intent_id="my-intent-123")
        assert graph.intent_id == "my-intent-123"

    def test_parse_capability(self):
        parser = DSLParser()
        graph = parser.parse(self.DSL_SIMPLE, intent_id="x")
        node = graph.nodes["AnalyzeNode"]
        assert node.capability == "code_analysis"

    def test_parse_cost(self):
        parser = DSLParser()
        graph = parser.parse(self.DSL_SIMPLE, intent_id="x")
        node = graph.nodes["AnalyzeNode"]
        assert node.estimated_cost == Decimal("0.50")

    def test_parse_duration(self):
        parser = DSLParser()
        graph = parser.parse(self.DSL_SIMPLE, intent_id="x")
        node = graph.nodes["AnalyzeNode"]
        assert node.estimated_duration_seconds == 60

    def test_parse_two_phase_creates_edge(self):
        parser = DSLParser()
        graph = parser.parse(self.DSL_TWO_PHASES, intent_id="mp")
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1  # Analyze → Implement

    def test_parse_no_intent_block_raises(self):
        parser = DSLParser()
        with pytest.raises(DSLParseError, match="No intent block"):
            parser.parse("not valid dsl", intent_id="x")

    def test_parse_total_cost_calculated(self):
        parser = DSLParser()
        graph = parser.parse(self.DSL_TWO_PHASES, intent_id="x")
        assert graph.total_estimated_cost == Decimal("1.00")


# ---------------------------------------------------------------------------
# intent_schema
# ---------------------------------------------------------------------------
from rct_control_plane.intent_schema import (
    BudgetSpec,
    ContextBundle,
    IntentConstraint,
    IntentObject,
    IntentPriority,
    IntentType,
    RiskProfile,
    ScopeObject,
    ScopeType,
)


class TestIntentSchema:
    def _make_intent(self, goal: str = "refactor auth module") -> IntentObject:
        return IntentObject(
            goal=goal,
            intent_type=IntentType.REFACTOR,
            scope=ScopeObject(scope_type=ScopeType.MODULE, target="auth/"),
            context=ContextBundle(user_id="u1", user_tier="PRO"),
        )

    def test_intent_object_creates(self):
        intent = self._make_intent()
        assert intent.goal == "refactor auth module"
        assert intent.intent_type == IntentType.REFACTOR

    def test_intent_id_auto_generated(self):
        i1 = self._make_intent()
        i2 = self._make_intent()
        assert i1.id != i2.id

    def test_intent_default_priority(self):
        intent = self._make_intent()
        assert intent.priority == IntentPriority.MEDIUM

    def test_intent_default_risk_profile(self):
        intent = self._make_intent()
        assert intent.risk_profile == RiskProfile.LOW

    def test_intent_empty_goal_raises(self):
        with pytest.raises(Exception):
            IntentObject(
                goal="",
                intent_type=IntentType.DEPLOY,
                scope=ScopeObject(scope_type=ScopeType.FILE, target="x.py"),
                context=ContextBundle(user_id="u", user_tier="FREE"),
            )

    def test_budget_spec_defaults(self):
        budget = BudgetSpec()
        assert budget.max_cost_usd is None
        assert budget.max_time is None

    def test_budget_spec_negative_cost_raises(self):
        with pytest.raises(Exception):
            BudgetSpec(max_cost_usd=Decimal("-5.00"))

    def test_scope_object_target(self):
        scope = ScopeObject(scope_type=ScopeType.FILE, target="src/main.py")
        assert scope.target == "src/main.py"

    def test_context_bundle_request_id_auto(self):
        ctx1 = ContextBundle(user_id="u", user_tier="FREE")
        ctx2 = ContextBundle(user_id="u", user_tier="FREE")
        assert ctx1.request_id != ctx2.request_id


# ---------------------------------------------------------------------------
# control_plane_state
# ---------------------------------------------------------------------------
from rct_control_plane.control_plane_state import (
    ControlPlanePhase,
    ControlPlaneState,
    TransitionResult,
    VALID_TRANSITIONS,
)


class TestControlPlaneState:
    def test_valid_transitions_defined(self):
        assert ControlPlanePhase.INTENT_RECEIVED in VALID_TRANSITIONS

    def test_initial_phase(self):
        state = ControlPlaneState(intent_id="i1")
        assert state.phase == ControlPlanePhase.INTENT_RECEIVED

    def test_valid_transition_succeeds(self):
        state = ControlPlaneState(intent_id="i1")
        result = state.transition_to(ControlPlanePhase.INTENT_COMPILED)
        assert result == TransitionResult.SUCCESS
        assert state.phase == ControlPlanePhase.INTENT_COMPILED

    def test_invalid_transition_rejected(self):
        state = ControlPlaneState(intent_id="i2")
        # Cannot jump from INTENT_RECEIVED to COMPLETED
        result = state.transition_to(ControlPlanePhase.COMPLETED)
        assert result == TransitionResult.INVALID_TRANSITION
        assert state.phase == ControlPlanePhase.INTENT_RECEIVED

    def test_cancel_from_any_active_phase(self):
        state = ControlPlaneState(intent_id="i3")
        result = state.transition_to(ControlPlanePhase.CANCELLED)
        assert result == TransitionResult.SUCCESS

    def test_fail_from_intent_received(self):
        state = ControlPlaneState(intent_id="i4")
        result = state.transition_to(ControlPlanePhase.FAILED)
        assert result == TransitionResult.SUCCESS
