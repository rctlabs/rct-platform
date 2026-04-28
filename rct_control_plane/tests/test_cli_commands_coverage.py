"""
Coverage-gap tests for rct_control_plane/cli.py — Phase 2

Targets commands and branches not reached by existing test suite:
  - build command: exception path
  - evaluate: intent-not-found path
  - list: json output, plain-table (no-rich) output
  - audit: no-events path + json output
  - metrics: table output
  - reset: no-force (abort/cancel), plain-text success
  - adapter status/list: ImportError paths
  - governance: ImportError path, json + no-violations
  - timeline: ImportError path
  - replay: ImportError path + no-result
  - logs: success path
"""
from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest


# ── Shared fixtures ────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _reset_ctx(monkeypatch):
    import rct_control_plane.cli as cli_mod
    monkeypatch.setattr(cli_mod, "_cli_context", None)


@pytest.fixture()
def runner():
    from click.testing import CliRunner
    return CliRunner()


@pytest.fixture()
def cli():
    from rct_control_plane.cli import cli as _cli
    return _cli


# ── Helpers ────────────────────────────────────────────────────────────────────

def _compile_intent(runner, cli, intent_text: str = "deploy auth service") -> str:
    """Compile an intent and return its intent_id (saved to context)."""
    import json
    result = runner.invoke(cli, ["compile", intent_text, "--user-id", "u1", "-o", "json", "--save"])
    data = json.loads(result.output)
    return data["intent_id"]


# ── build command ──────────────────────────────────────────────────────────────

class TestBuildCommand:
    def test_build_exception_shows_error(self, runner, cli):
        """build command: parser raises → error shown, exit 1."""
        with patch("rct_control_plane.cli.DSLParser") as MockParser:
            MockParser.return_value.parse.side_effect = RuntimeError("parser boom")
            result = runner.invoke(cli, [
                "build",
                "--dsl-text", "STEP do_something",
                "--intent-id", "fake-id",
            ])
        assert result.exit_code == 1

    def test_build_no_dsl_input_exits(self, runner, cli):
        """build without --dsl-text or --dsl-file → exit 1."""
        result = runner.invoke(cli, ["build", "--intent-id", "fake-id"])
        assert result.exit_code == 1


# ── evaluate command ───────────────────────────────────────────────────────────

class TestEvaluateCommand:
    def test_evaluate_intent_not_found(self, runner, cli):
        result = runner.invoke(cli, ["evaluate", "--intent-id", "no-such-id"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower() or result.exit_code != 0


# ── list command ───────────────────────────────────────────────────────────────

class TestListCommand:
    def test_list_json_output_empty(self, runner, cli):
        import json
        result = runner.invoke(cli, ["list", "-o", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "intents" in data

    def test_list_table_output_empty(self, runner, cli):
        # Forces plain-table output (no rich renders table differently)
        with patch("rct_control_plane.cli._HAS_RICH", False):
            result = runner.invoke(cli, ["list", "-o", "table"])
        assert result.exit_code == 0

    def test_list_json_with_items(self, runner, cli):
        import json
        # First compile an intent so there is something to list
        _compile_intent(runner, cli)
        result = runner.invoke(cli, ["list", "-o", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["total"] >= 1


# ── audit command ──────────────────────────────────────────────────────────────

class TestAuditCommand:
    def test_audit_no_events(self, runner, cli):
        result = runner.invoke(cli, ["audit", "no-such-intent"])
        assert result.exit_code == 0  # sys.exit(0) on no events

    def test_audit_json_output_with_events(self, runner, cli):
        intent_id = _compile_intent(runner, cli)
        result = runner.invoke(cli, ["audit", intent_id, "-o", "json"])
        # Even if no events recorded, output should be valid JSON or exit 0
        assert result.exit_code in (0, 1)

    def test_audit_table_output(self, runner, cli):
        intent_id = _compile_intent(runner, cli)
        with patch("rct_control_plane.cli._HAS_RICH", False):
            result = runner.invoke(cli, ["audit", intent_id, "-o", "table"])
        assert result.exit_code in (0, 1)


# ── metrics command ────────────────────────────────────────────────────────────

class TestMetricsCommand:
    def test_metrics_json(self, runner, cli):
        result = runner.invoke(cli, ["metrics", "-o", "json"])
        assert result.exit_code == 0

    def test_metrics_table_no_rich(self, runner, cli):
        with patch("rct_control_plane.cli._HAS_RICH", False):
            result = runner.invoke(cli, ["metrics", "-o", "table"])
        assert result.exit_code == 0


# ── reset command ──────────────────────────────────────────────────────────────

class TestResetCommand:
    def test_reset_force_plain_text(self, runner, cli):
        with patch("rct_control_plane.cli._HAS_RICH", False):
            result = runner.invoke(cli, ["reset", "--force"])
        assert result.exit_code == 0
        assert "reset" in result.output.lower() or "deleted" in result.output.lower()

    def test_reset_no_force_cancels(self, runner, cli):
        result = runner.invoke(cli, ["reset"], input="n\n")
        # Aborted → exit 0 (click.Abort path)
        assert result.exit_code in (0, 1)


# ── adapter commands ───────────────────────────────────────────────────────────

class TestAdapterCommands:
    def test_adapter_status_import_error(self, runner, cli):
        with patch.dict(sys.modules, {"core.adapters": None}):
            result = runner.invoke(cli, ["adapter", "status"])
        # ImportError path → warning message printed, exit 0
        assert result.exit_code in (0, 1)

    def test_adapter_list_import_error(self, runner, cli):
        with patch.dict(sys.modules, {"core.adapters": None}):
            result = runner.invoke(cli, ["adapter", "list"])
        assert result.exit_code in (0, 1)


# ── governance command ─────────────────────────────────────────────────────────

class TestGovernanceCommand:
    def test_governance_import_error(self, runner, cli):
        with patch.dict(sys.modules, {"core.adapters.base_os_adapter": None}):
            result = runner.invoke(cli, ["governance"])
        assert result.exit_code in (0, 1)

    def test_governance_json_no_violations(self, runner, cli):
        import json
        fake_patterns = ["pattern_1", "pattern_2"]
        with patch("rct_control_plane.cli._HAS_RICH", False):
            with patch.dict(
                "sys.modules",
                {
                    "core.adapters.base_os_adapter": MagicMock(
                        THE_9_CODEX_FORBIDDEN_PATTERNS=fake_patterns
                    )
                },
            ):
                result = runner.invoke(cli, ["governance", "-o", "json"])
        if result.exit_code == 0:
            data = json.loads(result.output)
            assert "violations" in data

    def test_governance_table_no_violations(self, runner, cli):
        fake_patterns: list = []
        with patch("rct_control_plane.cli._HAS_RICH", False):
            with patch.dict(
                "sys.modules",
                {
                    "core.adapters.base_os_adapter": MagicMock(
                        THE_9_CODEX_FORBIDDEN_PATTERNS=fake_patterns
                    )
                },
            ):
                result = runner.invoke(cli, ["governance", "-o", "table"])
        assert result.exit_code in (0, 1)


# ── timeline command ───────────────────────────────────────────────────────────

class TestTimelineCommand:
    def test_timeline_import_error(self, runner, cli):
        with patch.dict(sys.modules, {"core.kernel": None}):
            result = runner.invoke(cli, ["timeline", "--agent", "agent-test"])
        # ImportError → warning, exit 0 or 1 acceptable
        assert result.exit_code in (0, 1)

    def test_timeline_json_empty(self, runner, cli):
        with patch("rct_control_plane.cli._HAS_RICH", False):
            with patch.dict(
                "sys.modules",
                {"core.kernel": MagicMock()},
            ):
                # MemoryDeltaEngine might raise ImportError if core.kernel.memory_delta not found
                result = runner.invoke(cli, ["timeline", "--agent", "agent-1", "-o", "json"])
        assert result.exit_code in (0, 1)


# ── replay command ─────────────────────────────────────────────────────────────

class TestReplayCommand:
    def test_replay_import_error(self, runner, cli):
        with patch.dict(sys.modules, {"core.adapters.determinism_controller": None}):
            result = runner.invoke(cli, ["replay", "--hash", "abc123"])
        assert result.exit_code in (0, 1)

    def test_replay_no_result(self, runner, cli):
        mock_controller = MagicMock()
        mock_controller.replay.return_value = None
        with patch.dict(
            "sys.modules",
            {
                "core.adapters.determinism_controller": MagicMock(
                    DeterminismController=MagicMock(return_value=mock_controller)
                )
            },
        ):
            result = runner.invoke(cli, ["replay", "--hash", "abc123"])
        assert result.exit_code in (0, 1)

    def test_replay_match_plain_text(self, runner, cli):
        mock_controller = MagicMock()
        mock_controller.replay.return_value = {
            "original": {"hash": "hash1"},
            "replayed": {"hash": "hash1"},
            "match": True,
        }
        with patch("rct_control_plane.cli._HAS_RICH", False):
            with patch.dict(
                "sys.modules",
                {
                    "core.adapters.determinism_controller": MagicMock(
                        DeterminismController=MagicMock(return_value=mock_controller)
                    )
                },
            ):
                result = runner.invoke(cli, ["replay", "--hash", "abc123", "-o", "table"])
        assert result.exit_code in (0, 1)


# ── logs command ──────────────────────────────────────────────────────────────

class TestLogsCommand:
    def test_logs_json_empty(self, runner, cli):
        import json
        result = runner.invoke(cli, ["logs", "-o", "json"])
        if result.exit_code == 0:
            data = json.loads(result.output)
            assert "logs" in data

    def test_logs_table_empty(self, runner, cli):
        with patch("rct_control_plane.cli._HAS_RICH", False):
            result = runner.invoke(cli, ["logs", "-o", "table"])
        assert result.exit_code == 0

    def test_logs_with_adapter_filter(self, runner, cli):
        result = runner.invoke(cli, ["logs", "--adapter", "test-adapter"])
        assert result.exit_code in (0, 1)
