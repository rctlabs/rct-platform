"""
Tests for benchmark/enterprise_pillars.py

Covers all 4 Pillars:
  Pillar 1 — Cognitive Latency (p95 < 100ms)
  Pillar 2 — Governance Interrupt RTO (100% intercept, p95 < 10ms)
  Pillar 3 — Memory Compression Endurance (≥ 70%)
  Pillar 4 — Deterministic Integrity (100% match)

Also tests the PillarResult dataclass, run_all_pillars, and JSON output.
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from benchmark.enterprise_pillars import (
    PillarResult,
    run_pillar_1,
    run_pillar_2,
    run_pillar_3,
    run_pillar_4,
    run_all_pillars,
    PILLAR_RUNNERS,
)


# ---------------------------------------------------------------------------
# PillarResult
# ---------------------------------------------------------------------------

class TestPillarResult:
    def test_passed_status_string(self):
        r = PillarResult(pillar_id=1, name="Test", passed=True)
        assert r.to_dict()["status"] == "PASS"

    def test_failed_status_string(self):
        r = PillarResult(pillar_id=2, name="Test", passed=False)
        assert r.to_dict()["status"] == "FAIL"

    def test_to_dict_has_required_keys(self):
        r = PillarResult(pillar_id=3, name="Foo", passed=True, details={"x": 1})
        d = r.to_dict()
        assert "pillar_id" in d
        assert "name" in d
        assert "status" in d
        assert "details" in d
        assert "error" in d

    def test_error_field_passthrough(self):
        r = PillarResult(pillar_id=4, name="Bar", passed=False, error="boom")
        assert r.to_dict()["error"] == "boom"


# ---------------------------------------------------------------------------
# Pillar 1 — Cognitive Latency
# ---------------------------------------------------------------------------

class TestPillar1CognitiveLatency:
    def test_passes_with_default_runs(self):
        """FDIA pure Python scoring must be well under 100ms p95."""
        result = run_pillar_1(n_runs=100)
        assert result.pillar_id == 1
        assert result.passed is True, (
            f"Pillar 1 FAILED: p95={result.details.get('p95_ms')}ms"
        )

    def test_details_contain_latency_fields(self):
        result = run_pillar_1(n_runs=50)
        d = result.details
        assert "p50_ms" in d
        assert "p95_ms" in d
        assert "p99_ms" in d
        assert "threshold_ms" in d

    def test_p95_less_than_threshold(self):
        result = run_pillar_1(n_runs=100)
        assert result.details["p95_ms"] < result.details["threshold_ms"]

    def test_n_runs_recorded(self):
        result = run_pillar_1(n_runs=77)
        assert result.details["n_runs"] == 77

    def test_verbose_does_not_raise(self, capsys):
        run_pillar_1(n_runs=20, verbose=True)
        captured = capsys.readouterr()
        assert "Pillar 1" in captured.out

    def test_result_name_correct(self):
        result = run_pillar_1(n_runs=10)
        assert result.name == "Cognitive Latency"


# ---------------------------------------------------------------------------
# Pillar 2 — Governance Interrupt RTO
# ---------------------------------------------------------------------------

class TestPillar2GovernanceInterrupt:
    def test_passes_with_default_runs(self):
        """PolicyEvaluator must intercept SYSTEMIC intents every time, fast."""
        result = run_pillar_2(n_runs=50)
        assert result.pillar_id == 2
        assert result.passed is True, (
            f"Pillar 2 FAILED: rate={result.details.get('intercept_rate')}, "
            f"p95={result.details.get('p95_latency_ms')}ms"
        )

    def test_intercept_rate_is_one(self):
        result = run_pillar_2(n_runs=50)
        assert result.details["intercept_rate"] == 1.0

    def test_latency_under_threshold(self):
        result = run_pillar_2(n_runs=50)
        assert result.details["p95_latency_ms"] < result.details["threshold_latency_ms"]

    def test_details_keys_present(self):
        result = run_pillar_2(n_runs=20)
        d = result.details
        for key in ("n_runs", "intercepted", "intercept_rate", "p95_latency_ms"):
            assert key in d, f"Missing key: {key}"

    def test_intercepted_equals_n_runs(self):
        n = 30
        result = run_pillar_2(n_runs=n)
        assert result.details["intercepted"] == n

    def test_verbose_does_not_raise(self, capsys):
        run_pillar_2(n_runs=10, verbose=True)
        captured = capsys.readouterr()
        assert "Pillar 2" in captured.out

    def test_result_name_correct(self):
        result = run_pillar_2(n_runs=10)
        assert result.name == "Governance Interrupt RTO"


# ---------------------------------------------------------------------------
# Pillar 3 — Memory Compression Endurance
# ---------------------------------------------------------------------------

class TestPillar3Compression:
    def test_passes_at_medium_scale(self):
        """10 agents × 200 ticks = 2000 events — must compress ≥ 70%."""
        result = run_pillar_3(n_agents=10, n_ticks=200)
        assert result.pillar_id == 3
        assert result.passed is True, (
            f"Pillar 3 FAILED: ratio={result.details.get('compression_ratio')}"
        )

    def test_compression_ratio_gte_threshold(self):
        result = run_pillar_3(n_agents=5, n_ticks=100)
        assert result.details["compression_ratio"] >= result.details["threshold"]

    def test_total_events_correct(self):
        n_agents = 4
        n_ticks = 50
        result = run_pillar_3(n_agents=n_agents, n_ticks=n_ticks)
        # Total events = n_agents * n_ticks
        assert result.details["total_events"] == n_agents * n_ticks

    def test_state_replay_flag_true(self):
        result = run_pillar_3(n_agents=3, n_ticks=20)
        assert result.details["replay_ok"] is True

    def test_details_keys_present(self):
        result = run_pillar_3(n_agents=2, n_ticks=10)
        for key in ("n_agents", "n_ticks", "total_events", "compression_ratio", "threshold"):
            assert key in result.details

    def test_verbose_does_not_raise(self, capsys):
        run_pillar_3(n_agents=2, n_ticks=10, verbose=True)
        captured = capsys.readouterr()
        assert "Pillar 3" in captured.out

    def test_result_name_correct(self):
        result = run_pillar_3(n_agents=2, n_ticks=10)
        assert result.name == "Memory Compression Endurance"


# ---------------------------------------------------------------------------
# Pillar 4 — Deterministic Integrity
# ---------------------------------------------------------------------------

class TestPillar4Determinism:
    def test_passes_with_default_runs(self):
        """100% of rank_actions calls must return identical ordering."""
        result = run_pillar_4(n_runs=100)
        assert result.pillar_id == 4
        assert result.passed is True, (
            f"Pillar 4 FAILED: {result.details.get('mismatch_count')} mismatches"
        )

    def test_match_rate_is_one(self):
        result = run_pillar_4(n_runs=50)
        assert result.details["match_rate"] == 1.0

    def test_mismatch_count_is_zero(self):
        result = run_pillar_4(n_runs=50)
        assert result.details["mismatch_count"] == 0

    def test_reference_ranking_populated(self):
        result = run_pillar_4(n_runs=10)
        assert result.details["reference_ranking"] is not None
        assert len(result.details["reference_ranking"]) > 0

    def test_reference_ranking_is_sorted_descending(self):
        result = run_pillar_4(n_runs=10)
        scores = [s for _, s in result.details["reference_ranking"]]
        assert scores == sorted(scores, reverse=True)

    def test_details_keys_present(self):
        result = run_pillar_4(n_runs=10)
        for key in ("n_runs", "match_count", "mismatch_count", "match_rate"):
            assert key in result.details

    def test_verbose_does_not_raise(self, capsys):
        run_pillar_4(n_runs=10, verbose=True)
        captured = capsys.readouterr()
        assert "Pillar 4" in captured.out

    def test_result_name_correct(self):
        result = run_pillar_4(n_runs=5)
        assert result.name == "Deterministic Integrity"

    def test_second_independent_run_same_ranking(self):
        """Two independent runs must produce the same reference ranking."""
        r1 = run_pillar_4(n_runs=5)
        r2 = run_pillar_4(n_runs=5)
        assert r1.details["reference_ranking"] == r2.details["reference_ranking"]


# ---------------------------------------------------------------------------
# run_all_pillars
# ---------------------------------------------------------------------------

class TestRunAllPillars:
    def test_all_four_pillars_run(self):
        results = run_all_pillars(verbose=False)
        assert len(results) == 4
        ids = [r.pillar_id for r in results]
        assert sorted(ids) == [1, 2, 3, 4]

    def test_all_pass(self):
        results = run_all_pillars(verbose=False)
        for r in results:
            assert r.passed is True, f"Pillar {r.pillar_id} ({r.name}) FAILED: {r.details.get('result')}"

    def test_pillar_filter_single(self):
        results = run_all_pillars(pillar_filter=1)
        assert len(results) == 1
        assert results[0].pillar_id == 1

    def test_pillar_filter_pillar_4(self):
        results = run_all_pillars(pillar_filter=4)
        assert len(results) == 1
        assert results[0].pillar_id == 4

    def test_results_have_no_exceptions(self):
        results = run_all_pillars()
        for r in results:
            assert r.error is None, f"Pillar {r.pillar_id} raised: {r.error}"

    def test_to_dict_json_serialisable(self):
        results = run_all_pillars()
        for r in results:
            payload = r.to_dict()
            # Must be JSON-serialisable (no datetime, etc.)
            json_str = json.dumps(payload)
            assert isinstance(json_str, str)

    def test_pillar_runners_dict_complete(self):
        assert set(PILLAR_RUNNERS.keys()) == {1, 2, 3, 4}
