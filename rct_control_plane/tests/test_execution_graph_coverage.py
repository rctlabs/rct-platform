"""
Coverage boost tests for execution_graph_ir.py — uncovered lines.

Uncovered: 137-152 (is_ready), 156 (can_retry), 202 (to_dict edge),
257, 259 (add_edge validation), 272 (get_node), 284-288 (get_ready_nodes),
320 (topo cycle), 373-374, 379, 381 (validate errors),
392 (unreachable), 397-407 (data_flow validation),
484-542 (from_dict full reconstruction with resources)
"""
from __future__ import annotations

import pytest
from decimal import Decimal
from datetime import timedelta

from rct_control_plane.execution_graph_ir import (
    ExecutionGraph,
    ExecutionNode,
    DependencyEdge,
    DependencyType,
    NodeType,
    NodeStatus,
    ResourceRequirement,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────

def make_node(node_id, duration=10, status=NodeStatus.PENDING) -> ExecutionNode:
    return ExecutionNode(
        id=node_id,
        node_type=NodeType.AGENT_CAPABILITY,
        estimated_duration_seconds=duration,
        status=status,
    )


def make_graph(*node_ids) -> ExecutionGraph:
    g = ExecutionGraph(intent_id="test")
    for nid in node_ids:
        g.add_node(make_node(nid))
    return g


# ─────────────────────────────────────────────────────────────────────────────
# ExecutionNode.is_ready (lines 137-152)
# ─────────────────────────────────────────────────────────────────────────────

class TestIsReady:
    def test_pending_no_deps_is_ready(self):
        g = make_graph("A")
        assert g.nodes["A"].is_ready(set(), g) is True

    def test_non_pending_status_not_ready(self):
        g = make_graph("A")
        g.nodes["A"].status = NodeStatus.RUNNING
        assert g.nodes["A"].is_ready(set(), g) is False

    def test_dep_not_completed_not_ready(self):
        g = make_graph("A", "B")
        g.add_edge(DependencyEdge(from_node="A", to_node="B"))
        # "A" not in completed_nodes
        assert g.nodes["B"].is_ready(set(), g) is False

    def test_dep_completed_is_ready(self):
        g = make_graph("A", "B")
        g.add_edge(DependencyEdge(from_node="A", to_node="B"))
        assert g.nodes["B"].is_ready({"A"}, g) is True

    def test_multiple_deps_all_needed(self):
        g = make_graph("A", "B", "C")
        g.add_edge(DependencyEdge(from_node="A", to_node="C"))
        g.add_edge(DependencyEdge(from_node="B", to_node="C"))
        assert g.nodes["C"].is_ready({"A"}, g) is False
        assert g.nodes["C"].is_ready({"A", "B"}, g) is True


# ─────────────────────────────────────────────────────────────────────────────
# ExecutionNode.can_retry (line 156)
# ─────────────────────────────────────────────────────────────────────────────

class TestCanRetry:
    def test_failed_under_max_can_retry(self):
        node = make_node("A", status=NodeStatus.FAILED)
        node.retry_count = 1
        node.max_retries = 3
        assert node.can_retry() is True

    def test_failed_at_max_cannot_retry(self):
        node = make_node("A", status=NodeStatus.FAILED)
        node.retry_count = 3
        node.max_retries = 3
        assert node.can_retry() is False

    def test_completed_cannot_retry(self):
        node = make_node("A", status=NodeStatus.COMPLETED)
        assert node.can_retry() is False


# ─────────────────────────────────────────────────────────────────────────────
# DependencyEdge.to_dict (line 202)
# ─────────────────────────────────────────────────────────────────────────────

class TestDependencyEdgeToDict:
    def test_to_dict_has_all_fields(self):
        edge = DependencyEdge(
            from_node="A", to_node="B",
            dependency_type=DependencyType.DATA_FLOW,
            data_mapping={"output_key": "input_key"},
            condition="status == 'success'",
            metadata={"info": "test"},
        )
        d = edge.to_dict()
        assert d["from_node"] == "A"
        assert d["to_node"] == "B"
        assert d["dependency_type"] == "data_flow"
        assert d["data_mapping"] == {"output_key": "input_key"}
        assert d["condition"] == "status == 'success'"
        assert d["metadata"] == {"info": "test"}


# ─────────────────────────────────────────────────────────────────────────────
# ExecutionGraph.add_edge — validation errors (257, 259)
# ─────────────────────────────────────────────────────────────────────────────

class TestAddEdgeValidation:
    def test_add_edge_missing_from_node_raises(self):
        g = make_graph("B")
        with pytest.raises(ValueError, match="Source node"):
            g.add_edge(DependencyEdge(from_node="NONEXISTENT", to_node="B"))

    def test_add_edge_missing_to_node_raises(self):
        g = make_graph("A")
        with pytest.raises(ValueError, match="Target node"):
            g.add_edge(DependencyEdge(from_node="A", to_node="NONEXISTENT"))

    def test_add_edge_creates_cycle_raises(self):
        g = make_graph("A", "B")
        g.add_edge(DependencyEdge(from_node="A", to_node="B"))
        with pytest.raises(ValueError, match="cycle"):
            g.add_edge(DependencyEdge(from_node="B", to_node="A"))

    def test_add_duplicate_node_raises(self):
        g = make_graph("A")
        with pytest.raises(ValueError, match="already exists"):
            g.add_node(make_node("A"))


# ─────────────────────────────────────────────────────────────────────────────
# get_node (line 272)
# ─────────────────────────────────────────────────────────────────────────────

class TestGetNode:
    def test_get_existing_node(self):
        g = make_graph("X")
        node = g.get_node("X")
        assert node is not None
        assert node.id == "X"

    def test_get_missing_node_returns_none(self):
        g = make_graph("X")
        assert g.get_node("MISSING") is None


# ─────────────────────────────────────────────────────────────────────────────
# get_ready_nodes (lines 284-288)
# ─────────────────────────────────────────────────────────────────────────────

class TestGetReadyNodes:
    def test_ready_nodes_with_no_deps(self):
        g = make_graph("A", "B")
        ready = g.get_ready_nodes(set())
        ready_ids = [n.id for n in ready]
        assert "A" in ready_ids
        assert "B" in ready_ids

    def test_ready_nodes_excludes_completed(self):
        g = make_graph("A", "B")
        ready = g.get_ready_nodes({"A"})
        ready_ids = [n.id for n in ready]
        assert "A" not in ready_ids

    def test_ready_nodes_after_dep_completed(self):
        g = make_graph("A", "B")
        g.add_edge(DependencyEdge(from_node="A", to_node="B"))
        ready_before = [n.id for n in g.get_ready_nodes(set())]
        assert "B" not in ready_before

        ready_after = [n.id for n in g.get_ready_nodes({"A"})]
        assert "B" in ready_after


# ─────────────────────────────────────────────────────────────────────────────
# topological_sort — cycle error (line 320)
# ─────────────────────────────────────────────────────────────────────────────

class TestTopologicalSort:
    def test_topo_sort_linear(self):
        g = make_graph("A", "B", "C")
        g.add_edge(DependencyEdge(from_node="A", to_node="B"))
        g.add_edge(DependencyEdge(from_node="B", to_node="C"))
        order = g.topological_sort()
        assert order.index("A") < order.index("B")
        assert order.index("B") < order.index("C")

    def test_topo_sort_empty_graph(self):
        g = ExecutionGraph(intent_id="empty")
        assert g.topological_sort() == []


# ─────────────────────────────────────────────────────────────────────────────
# validate — error paths (373-374, 379, 381, 392, 397-407)
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateErrors:
    def test_empty_graph_valid(self):
        g = ExecutionGraph(intent_id="empty")
        errors = g.validate()
        assert errors == []

    def test_data_flow_edge_valid_mapping(self):
        g = ExecutionGraph(intent_id="df")
        n1 = ExecutionNode(
            id="N1", node_type=NodeType.AGENT_CAPABILITY,
            produces_outputs=["report"]
        )
        n2 = ExecutionNode(
            id="N2", node_type=NodeType.TOOL_CALL,
            required_inputs=["report"]
        )
        g.add_node(n1)
        g.add_node(n2)
        edge = DependencyEdge(
            from_node="N1", to_node="N2",
            dependency_type=DependencyType.DATA_FLOW,
            data_mapping={"report": "report"}
        )
        g.add_edge(edge)
        errors = g.validate()
        # Should have no data-flow errors (report is in produces_outputs and required_inputs)
        assert all("Data flow" not in e for e in errors)

    def test_data_flow_bad_from_output_error(self):
        g = ExecutionGraph(intent_id="df_bad")
        n1 = ExecutionNode(id="N1", node_type=NodeType.AGENT_CAPABILITY, produces_outputs=[])
        n2 = ExecutionNode(id="N2", node_type=NodeType.TOOL_CALL, required_inputs=["report"])
        g.add_node(n1)
        g.add_node(n2)
        edge = DependencyEdge(
            from_node="N1", to_node="N2",
            dependency_type=DependencyType.DATA_FLOW,
            data_mapping={"report": "report"}  # N1 doesn't produce "report"
        )
        g.add_edge(edge)
        errors = g.validate()
        assert any("doesn't produce" in e for e in errors)

    def test_data_flow_bad_to_input_error(self):
        g = ExecutionGraph(intent_id="df_bad2")
        n1 = ExecutionNode(id="N1", node_type=NodeType.AGENT_CAPABILITY, produces_outputs=["report"])
        n2 = ExecutionNode(id="N2", node_type=NodeType.TOOL_CALL, required_inputs=[])   # doesn't require "report"
        g.add_node(n1)
        g.add_node(n2)
        edge = DependencyEdge(
            from_node="N1", to_node="N2",
            dependency_type=DependencyType.DATA_FLOW,
            data_mapping={"report": "report"}
        )
        g.add_edge(edge)
        errors = g.validate()
        assert any("doesn't require" in e for e in errors)


# ─────────────────────────────────────────────────────────────────────────────
# calculate_critical_path
# ─────────────────────────────────────────────────────────────────────────────

class TestCalculateCriticalPath:
    def test_single_node_critical_path(self):
        g = make_graph("A")
        g.nodes["A"].estimated_duration_seconds = 30
        assert g.calculate_critical_path() == 30

    def test_serial_nodes_critical_path(self):
        g = ExecutionGraph(intent_id="cp")
        for nid, dur in [("A", 10), ("B", 20), ("C", 15)]:
            n = make_node(nid, duration=dur)
            g.add_node(n)
        g.add_edge(DependencyEdge(from_node="A", to_node="B"))
        g.add_edge(DependencyEdge(from_node="B", to_node="C"))
        # Critical path: A(10) + B(20) + C(15) = 45
        assert g.calculate_critical_path() == 45


# ─────────────────────────────────────────────────────────────────────────────
# from_dict (lines 484-542) — full deserialization
# ─────────────────────────────────────────────────────────────────────────────

class TestFromDict:
    def test_roundtrip_simple(self):
        g = make_graph("A", "B")
        g.add_edge(DependencyEdge(from_node="A", to_node="B"))
        d = g.to_dict()
        restored = ExecutionGraph.from_dict(d)
        assert restored.intent_id == g.intent_id
        assert len(restored.nodes) == 2
        assert len(restored.edges) == 1

    def test_from_dict_with_resources(self):
        """Test that from_dict correctly deserializes resource requirements."""
        g = ExecutionGraph(intent_id="res")
        node = ExecutionNode(
            id="worker",
            node_type=NodeType.AGENT_CAPABILITY,
            resources=ResourceRequirement(
                max_memory_mb=2048,
                max_cpu_cores=4.0,
                max_tokens=8192,
                requires_gpu=True,
                max_cost_usd=Decimal("0.50"),
                max_time=timedelta(seconds=120),
            ),
            estimated_cost=Decimal("0.50"),
            estimated_duration_seconds=60,
        )
        g.add_node(node)
        d = g.to_dict()
        restored = ExecutionGraph.from_dict(d)
        r = restored.nodes["worker"].resources
        assert r.max_memory_mb == 2048
        assert r.max_cpu_cores == 4.0
        assert r.max_tokens == 8192
        assert r.requires_gpu is True

    def test_from_dict_preserves_metadata(self):
        g = ExecutionGraph(intent_id="m", metadata={"custom": "value"})
        g.add_node(make_node("A"))
        d = g.to_dict()
        restored = ExecutionGraph.from_dict(d)
        assert restored.metadata.get("custom") == "value"

    def test_from_dict_preserves_optimized_flag(self):
        g = ExecutionGraph(intent_id="o")
        g.optimized = True
        g.add_node(make_node("A"))
        d = g.to_dict()
        restored = ExecutionGraph.from_dict(d)
        assert restored.optimized is True

    def test_from_dict_with_different_node_types(self):
        g = ExecutionGraph(intent_id="nt")
        for node_type in [NodeType.TOOL_CALL, NodeType.CHECKPOINT, NodeType.APPROVAL_GATE]:
            n = ExecutionNode(id=node_type.value, node_type=node_type)
            g.add_node(n)
        d = g.to_dict()
        restored = ExecutionGraph.from_dict(d)
        assert restored.nodes[NodeType.TOOL_CALL.value].node_type == NodeType.TOOL_CALL

    def test_from_dict_edge_dependency_types(self):
        g = make_graph("A", "B")
        g.add_edge(DependencyEdge(
            from_node="A", to_node="B",
            dependency_type=DependencyType.CONTROL_FLOW,
            condition="result == 'ok'"
        ))
        d = g.to_dict()
        restored = ExecutionGraph.from_dict(d)
        assert restored.edges[0].dependency_type == DependencyType.CONTROL_FLOW
        assert restored.edges[0].condition == "result == 'ok'"


# ─────────────────────────────────────────────────────────────────────────────
# ResourceRequirement.to_dict (lines 88-95)
# ─────────────────────────────────────────────────────────────────────────────

class TestResourceRequirementToDict:
    def test_all_none_by_default(self):
        r = ResourceRequirement()
        d = r.to_dict()
        assert d["max_cost_usd"] is None
        assert d["max_time"] is None
        assert d["max_memory_mb"] is None
        assert d["requires_gpu"] is False

    def test_with_values(self):
        r = ResourceRequirement(
            max_cost_usd=Decimal("1.00"),
            max_time=timedelta(seconds=60),
            max_memory_mb=512,
            max_cpu_cores=2.5,
            max_tokens=4096,
            requires_gpu=True,
        )
        d = r.to_dict()
        assert d["max_cost_usd"] == "1.00"
        assert d["max_time"] == 60.0
        assert d["max_memory_mb"] == 512
        assert d["max_cpu_cores"] == 2.5
        assert d["max_tokens"] == 4096
        assert d["requires_gpu"] is True


# ─────────────────────────────────────────────────────────────────────────────
# ExecutionNode.to_dict
# ─────────────────────────────────────────────────────────────────────────────

class TestExecutionNodeToDict:
    def test_to_dict_complete(self):
        node = ExecutionNode(
            id="n1",
            node_type=NodeType.TOOL_CALL,
            tool_name="git_commit",
            parameters={"msg": "test"},
            required_inputs=["diff"],
            produces_outputs=["commit_sha"],
            estimated_cost=Decimal("0.25"),
            estimated_duration_seconds=5,
            description="Make a commit",
        )
        d = node.to_dict()
        assert d["id"] == "n1"
        assert d["tool_name"] == "git_commit"
        assert d["estimated_cost"] == "0.25"
        assert d["status"] == "pending"
