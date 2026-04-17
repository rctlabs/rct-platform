# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.1a0] - 2026-04-17

### Fixed
- `FDIAScorer.score_action()` now accepts legacy `other_agents_intents` (dict) and `governance_score` kwargs; `world_resources` is now optional (default `{}`)
- `FDIAScorer` — added `select_best_action()` method returning highest-scoring action or `None`
- `RegionalModelRouter` — added `route(language, region)` convenience method returning `model_id` string
- `ExecutionGraph.add_node()` now raises `ValueError` when duplicate node ID is added
- `ExecutionGraph.validate()` now treats empty graph as valid (no error)
- `TierRouter._calculate_risk_level()` guards against `artifact_content=None` (no more `AttributeError`)
- `SignedAIRegistry` — added `get_tier_config()` alias accepting both `SignedAITier` and `TierLevel` enums
- `rct_control_plane/api.py` — suppressed false-positive Bandit B104 on dev-server bind

### Added
- `rct_control_plane/tests/test_formatters_dsl.py` — 42 tests for `rich_formatter.py` (full coverage) and `dsl_parser.py`

### Changed
- CI `--cov-fail-under` raised from `20` → `70` (actual coverage: 71%)
- Test suite: 141 → **591 passed**, 0 failures
- Coverage: 28% → **89%**
- `pyproject.toml` testpaths now includes all test directories

## [1.0.0-alpha] - 2026-04-13

### Added
- Initial public release of RCT Platform SDK
- Core modules: FDIA Engine, Delta Engine, Regional Adapter
- SignedAI consensus framework (S/4/6/8 tier)
- 5 reference microservices: intent-loop, analysearch-intent, vector-search, crystallizer, gateway-api
- OpenAPI 3.1.0 contract specification
- Public benchmark suite (RCT_benchmark_public)
- Whitepapers: Foundation (01) and Architecture (02)
- rct_control_plane: intent_schema, dsl_parser, execution_graph_ir
- GitHub Actions: CI pipeline + security scanning
- Contributing guide and security policy

[1.0.0-alpha]: https://github.com/rctlabs/rct-platform/releases/tag/v1.0.0-alpha
