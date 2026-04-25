"""
Additional DSL Parser coverage tests — targets uncovered code paths.

Specifically covers:
- _parse_string (unquoted), _parse_number error, _parse_duration plain number
- _parse_array: empty array, no-bracket, quoted items
- _parse_parameters_block: bool/float/list/int/fallback
- _parse_node_parameter: all key branches (tool_name, description, max_retries, resources, etc.)
- _build_execution_node resource fields
- _calculate_graph_metrics: dependency edges, missing dep error, cycle detection
- format_graph: all node type branches, cost/timeout/deps/artifacts/description
- quick_parse convenience function
- DSLParseError with line/col info
- _extract_block unmatched brace error
- Nodes with no phases (direct node parsing)
- Observer event firing path
"""
from __future__ import annotations

import pytest
from rct_control_plane.dsl_parser import DSLParser, DSLParseError, quick_parse
from rct_control_plane.execution_graph_ir import NodeType


# ---------------------------------------------------------------------------
# DSLParseError construction
# ---------------------------------------------------------------------------

class TestDSLParseError:
    def test_error_without_line(self):
        err = DSLParseError("generic error")
        assert "generic error" in str(err)

    def test_error_with_line_and_col(self):
        err = DSLParseError("syntax fail", line=5, column=12)
        msg = str(err)
        assert "5" in msg
        assert "12" in msg
        assert "syntax fail" in msg

    def test_error_with_line_zero(self):
        err = DSLParseError("no line", line=0, column=0)
        assert "no line" in str(err)


# ---------------------------------------------------------------------------
# _extract_block: unmatched brace
# ---------------------------------------------------------------------------

class TestExtractBlock:
    def test_unmatched_brace_raises(self):
        parser = DSLParser()
        # Text with no closing brace — depth never reaches 0
        with pytest.raises(DSLParseError, match="Unmatched"):
            parser._extract_block("{ unclosed content", 0)

    def test_matched_brace_returns_content(self):
        parser = DSLParser()
        # _extract_block expects text starting AFTER the outer '{', with depth=1
        # So pass the full text and set start_idx=1 (past the opening brace)
        text = "{ inner content }"
        # Start at index 1 (past '{'), depth starts at 1
        result = parser._extract_block(text, 1)
        assert "inner content" in result


# ---------------------------------------------------------------------------
# _parse_string
# ---------------------------------------------------------------------------

class TestParseString:
    def test_quoted_string(self):
        parser = DSLParser()
        assert parser._parse_string('"hello world"') == "hello world"

    def test_unquoted_string_returned_as_is(self):
        parser = DSLParser()
        assert parser._parse_string("unquoted") == "unquoted"

    def test_empty_string(self):
        parser = DSLParser()
        assert parser._parse_string('""') == ""


# ---------------------------------------------------------------------------
# _parse_number
# ---------------------------------------------------------------------------

class TestParseNumber:
    def test_integer_string(self):
        parser = DSLParser()
        assert parser._parse_number("42") == "42"

    def test_float_string(self):
        parser = DSLParser()
        assert parser._parse_number("3.14") == "3.14"

    def test_invalid_number_raises(self):
        parser = DSLParser()
        with pytest.raises(DSLParseError, match="Invalid number"):
            parser._parse_number("not_a_number")


# ---------------------------------------------------------------------------
# _parse_duration
# ---------------------------------------------------------------------------

class TestParseDuration:
    def test_with_seconds_suffix(self):
        parser = DSLParser()
        assert parser._parse_duration("60s") == 60

    def test_plain_number(self):
        parser = DSLParser()
        assert parser._parse_duration("120") == 120


# ---------------------------------------------------------------------------
# _parse_array
# ---------------------------------------------------------------------------

class TestParseArray:
    def test_empty_array(self):
        parser = DSLParser()
        assert parser._parse_array("[]") == []

    def test_array_no_bracket(self):
        parser = DSLParser()
        # No brackets — returns []
        result = parser._parse_array("NodeA, NodeB")
        assert result == []

    def test_quoted_items(self):
        parser = DSLParser()
        result = parser._parse_array('["artifact1", "artifact2"]')
        assert "artifact1" in result
        assert "artifact2" in result

    def test_unquoted_items(self):
        parser = DSLParser()
        result = parser._parse_array("[NodeA, NodeB]")
        assert "NodeA" in result
        assert "NodeB" in result


# ---------------------------------------------------------------------------
# _parse_parameters_block
# ---------------------------------------------------------------------------

class TestParseParametersBlock:
    def test_string_param(self):
        parser = DSLParser()
        params = parser._parse_parameters_block('model = "gpt-4"')
        assert params["model"] == "gpt-4"

    def test_bool_true_param(self):
        parser = DSLParser()
        params = parser._parse_parameters_block("streaming = true")
        assert params["streaming"] is True

    def test_bool_false_param(self):
        parser = DSLParser()
        params = parser._parse_parameters_block("streaming = false")
        assert params["streaming"] is False

    def test_float_param(self):
        parser = DSLParser()
        params = parser._parse_parameters_block("temperature = 0.7")
        assert params["temperature"] == pytest.approx(0.7)

    def test_int_param(self):
        parser = DSLParser()
        params = parser._parse_parameters_block("max_tokens = 1024")
        assert params["max_tokens"] == 1024

    def test_array_param(self):
        parser = DSLParser()
        params = parser._parse_parameters_block("formats = [json, csv]")
        assert "formats" in params
        assert isinstance(params["formats"], list)

    def test_comment_line_skipped(self):
        parser = DSLParser()
        body = "// This is a comment\nkey = 10"
        params = parser._parse_parameters_block(body)
        assert params.get("key") == 10

    def test_fallback_string_on_non_int(self):
        parser = DSLParser()
        params = parser._parse_parameters_block("label = some_text")
        assert params["label"] == "some_text"


# ---------------------------------------------------------------------------
# _parse_node_parameter: all key branches
# ---------------------------------------------------------------------------

class TestParseNodeParameter:
    def _make_node_data(self):
        return {
            "id": "TestNode",
            "node_type": NodeType.AGENT_CAPABILITY,
            "metadata": {},
            "parameters": {},
        }

    def test_agent_capability(self):
        parser = DSLParser()
        nd = self._make_node_data()
        parser._parse_node_parameter("agent_capability", '"code_review"', nd)
        assert nd["node_type"] == NodeType.AGENT_CAPABILITY
        assert nd["capability"] == "code_review"

    def test_tool_name(self):
        parser = DSLParser()
        nd = self._make_node_data()
        parser._parse_node_parameter("tool_name", '"my_tool"', nd)
        assert nd["node_type"] == NodeType.TOOL_CALL
        assert nd["tool_name"] == "my_tool"

    def test_node_type_directly(self):
        parser = DSLParser()
        nd = self._make_node_data()
        parser._parse_node_parameter("node_type", '"tool_call"', nd)
        assert nd["node_type"] == NodeType.TOOL_CALL

    def test_cost(self):
        parser = DSLParser()
        nd = self._make_node_data()
        parser._parse_node_parameter("cost", "1.25", nd)
        from decimal import Decimal
        assert nd["estimated_cost"] == Decimal("1.25")

    def test_timeout(self):
        parser = DSLParser()
        nd = self._make_node_data()
        parser._parse_node_parameter("timeout", "90s", nd)
        assert nd["estimated_duration_seconds"] == 90

    def test_duration_alias(self):
        parser = DSLParser()
        nd = self._make_node_data()
        parser._parse_node_parameter("duration", "45s", nd)
        assert nd["estimated_duration_seconds"] == 45

    def test_depends_on(self):
        parser = DSLParser()
        nd = self._make_node_data()
        parser._parse_node_parameter("depends_on", "[NodeA, NodeB]", nd)
        assert "NodeA" in nd["dependencies"]
        assert "NodeB" in nd["dependencies"]

    def test_produces_artifacts(self):
        parser = DSLParser()
        nd = self._make_node_data()
        parser._parse_node_parameter("produces_artifacts", '["report.pdf"]', nd)
        assert "report.pdf" in nd["produces_outputs"]

    def test_requires_artifacts(self):
        parser = DSLParser()
        nd = self._make_node_data()
        parser._parse_node_parameter("requires_artifacts", '["input.json"]', nd)
        assert "input.json" in nd["required_inputs"]

    def test_description(self):
        parser = DSLParser()
        nd = self._make_node_data()
        parser._parse_node_parameter("description", '"This is a description"', nd)
        assert nd["description"] == "This is a description"

    def test_max_retries(self):
        parser = DSLParser()
        nd = self._make_node_data()
        parser._parse_node_parameter("max_retries", "5", nd)
        assert nd["max_retries"] == 5

    def test_max_memory_mb(self):
        parser = DSLParser()
        nd = self._make_node_data()
        parser._parse_node_parameter("max_memory_mb", "2048", nd)
        assert nd["resources"]["max_memory_mb"] == 2048

    def test_max_cpu_cores(self):
        parser = DSLParser()
        nd = self._make_node_data()
        parser._parse_node_parameter("max_cpu_cores", "4", nd)
        assert nd["resources"]["max_cpu_cores"] == 4.0

    def test_max_tokens(self):
        parser = DSLParser()
        nd = self._make_node_data()
        parser._parse_node_parameter("max_tokens", "8192", nd)
        assert nd["resources"]["max_tokens"] == 8192

    def test_requires_gpu_true(self):
        parser = DSLParser()
        nd = self._make_node_data()
        parser._parse_node_parameter("requires_gpu", "true", nd)
        assert nd["resources"]["requires_gpu"] is True

    def test_requires_gpu_false(self):
        parser = DSLParser()
        nd = self._make_node_data()
        parser._parse_node_parameter("requires_gpu", "false", nd)
        assert nd["resources"]["requires_gpu"] is False

    def test_unknown_key_goes_to_metadata(self):
        parser = DSLParser()
        nd = self._make_node_data()
        parser._parse_node_parameter("custom_label", "my_value", nd)
        assert nd["metadata"]["custom_label"] == "my_value"

    def test_parameters_key_ignored(self):
        """'parameters' key in node body is a no-op."""
        parser = DSLParser()
        nd = self._make_node_data()
        # Should not raise
        parser._parse_node_parameter("parameters", "{}", nd)


# ---------------------------------------------------------------------------
# Full parse: nodes without phases (direct nodes in intent body)
# ---------------------------------------------------------------------------

NO_PHASE_DSL = '''
intent "no_phase_intent" {
    node DirectNode {
        agent_capability = "direct_processing"
        cost = 0.10
    }
}
'''


class TestNoPhaseNodes:
    def test_parse_no_phase(self):
        parser = DSLParser()
        graph = parser.parse(NO_PHASE_DSL, intent_id="np-001")
        assert len(graph.nodes) == 1

    def test_node_has_correct_cost(self):
        parser = DSLParser()
        graph = parser.parse(NO_PHASE_DSL, intent_id="np-002")
        node = list(graph.nodes.values())[0]
        assert float(node.estimated_cost) == pytest.approx(0.10)


# ---------------------------------------------------------------------------
# _calculate_graph_metrics: nonexistent dependency error
# ---------------------------------------------------------------------------

BAD_DEP_DSL = '''
intent "bad_dep" {
    phase work {
        node NodeX {
            agent_capability = "analyze"
            depends_on = [NonExistentNode]
        }
    }
}
'''


class TestCalculateGraphMetrics:
    def test_missing_dependency_raises(self):
        parser = DSLParser()
        with pytest.raises(DSLParseError):
            parser.parse(BAD_DEP_DSL, intent_id="bd-001")


# ---------------------------------------------------------------------------
# format_graph: all branches
# ---------------------------------------------------------------------------

FULL_DSL = '''
intent "full_pipeline" {
    phase analyze {
        node AnalyzeNode {
            agent_capability = "code_analysis"
            cost = 0.50
            timeout = 60s
            produces_artifacts = ["analysis_report"]
            description = "Analyze the codebase"
        }
        node LintNode {
            tool_name = "ruff_linter"
            cost = 0.10
            timeout = 30s
            depends_on = [AnalyzeNode]
            requires_artifacts = ["analysis_report"]
        }
    }
    phase output {
        node SummaryNode {
            node_type = "agent_capability"
            cost = 0.25
        }
    }
}
'''


class TestFormatGraph:
    def test_format_returns_string(self):
        parser = DSLParser()
        graph = parser.parse(FULL_DSL, intent_id="fg-001")
        output = parser.format_graph(graph)
        assert isinstance(output, str)

    def test_format_contains_intent_keyword(self):
        parser = DSLParser()
        graph = parser.parse(FULL_DSL, intent_id="fg-002")
        output = parser.format_graph(graph)
        assert "intent" in output

    def test_format_contains_node_ids(self):
        parser = DSLParser()
        graph = parser.parse(FULL_DSL, intent_id="fg-003")
        output = parser.format_graph(graph)
        assert "AnalyzeNode" in output
        assert "LintNode" in output

    def test_format_contains_agent_capability(self):
        parser = DSLParser()
        graph = parser.parse(FULL_DSL, intent_id="fg-004")
        output = parser.format_graph(graph)
        assert "agent_capability" in output

    def test_format_contains_tool_name(self):
        parser = DSLParser()
        graph = parser.parse(FULL_DSL, intent_id="fg-005")
        output = parser.format_graph(graph)
        assert "tool_name" in output

    def test_format_contains_cost(self):
        parser = DSLParser()
        graph = parser.parse(FULL_DSL, intent_id="fg-006")
        output = parser.format_graph(graph)
        assert "cost" in output

    def test_format_contains_timeout(self):
        parser = DSLParser()
        graph = parser.parse(FULL_DSL, intent_id="fg-007")
        output = parser.format_graph(graph)
        assert "timeout" in output

    def test_format_contains_artifacts(self):
        parser = DSLParser()
        graph = parser.parse(FULL_DSL, intent_id="fg-008")
        output = parser.format_graph(graph)
        assert "produces_artifacts" in output or "analysis_report" in output

    def test_format_contains_description(self):
        parser = DSLParser()
        graph = parser.parse(FULL_DSL, intent_id="fg-009")
        output = parser.format_graph(graph)
        assert "description" in output or "Analyze the codebase" in output

    def test_format_contains_depends_on(self):
        parser = DSLParser()
        graph = parser.parse(FULL_DSL, intent_id="fg-010")
        output = parser.format_graph(graph)
        assert "depends_on" in output


# ---------------------------------------------------------------------------
# Parameters block in DSL
# ---------------------------------------------------------------------------

PARAMS_DSL = '''
intent "params_test" {
    phase run {
        node ParamNode {
            agent_capability = "llm_call"
            parameters {
                model = "gpt-4",
                temperature = 0.7,
                max_tokens = 2048,
                streaming = true,
                formats = [json, csv]
            }
        }
    }
}
'''


class TestParametersBlock:
    def test_parse_parameters_block_in_dsl(self):
        parser = DSLParser()
        graph = parser.parse(PARAMS_DSL, intent_id="pb-001")
        node = graph.nodes["ParamNode"]
        assert isinstance(node.parameters, dict)

    def test_parameters_model_parsed(self):
        parser = DSLParser()
        graph = parser.parse(PARAMS_DSL, intent_id="pb-002")
        node = graph.nodes["ParamNode"]
        assert node.parameters.get("model") == "gpt-4"


# ---------------------------------------------------------------------------
# quick_parse convenience function
# ---------------------------------------------------------------------------

class TestQuickParse:
    def test_quick_parse_success(self):
        dsl = '''
intent "quick" {
    phase run {
        node QuickNode {
            agent_capability = "run"
        }
    }
}
'''
        graph = quick_parse(dsl, "qp-001")
        assert graph is not None
        assert "QuickNode" in graph.nodes

    def test_quick_parse_invalid_raises(self):
        with pytest.raises(DSLParseError):
            quick_parse("not valid dsl", "qp-002")


# ---------------------------------------------------------------------------
# Observer integration 
# ---------------------------------------------------------------------------

class TestDSLParserObserver:
    def test_observer_receives_event(self):
        """Verify that when an observer is attached, GRAPH_BUILT event fires."""
        from unittest.mock import MagicMock

        mock_observer = MagicMock()

        parser = DSLParser(observer=mock_observer)
        dsl = '''
intent "observer_test" {
    phase run {
        node ONode {
            agent_capability = "observe"
        }
    }
}
'''
        parser.parse(dsl, intent_id="obs-001")
        # Observer should have been called once
        mock_observer.observe_event.assert_called_once()
        call_kwargs = mock_observer.observe_event.call_args[1]
        assert call_kwargs["success"] is True

    def test_no_observer_no_error(self):
        """Parser without observer should work without errors."""
        parser = DSLParser(observer=None)
        dsl = '''
intent "no_obs" {
    phase run {
        node N1 {
            agent_capability = "run"
        }
    }
}
'''
        graph = parser.parse(dsl, intent_id="no-obs-001")
        assert graph is not None
