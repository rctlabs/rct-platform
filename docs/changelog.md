# Changelog

All notable changes to RCT Platform are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [1.0.1a0] — 2026-04-17

### Fixed
- `FDIAScorer.score_action()` — accepts legacy `other_agents_intents` and `governance_score` kwargs; `world_resources` is now optional (default `{}`)
- `FDIAScorer.select_best_action()` — new method returning highest-scoring action or `None`
- `RegionalModelRouter.route(language, region)` — new convenience method returning `model_id`
- `ExecutionGraph.add_node()` — raises `ValueError` on duplicate node ID
- `ExecutionGraph.validate()` — empty graph is now valid
- `TierRouter._calculate_risk_level()` — guards against `artifact_content=None`
- `SignedAIRegistry.get_tier_config()` — accepts both `SignedAITier` and `TierLevel` enums
- `rct_control_plane/api.py` — suppressed false-positive Bandit B104 on dev-server bind
- **Python 3.12:** `datetime.utcnow()` → `datetime.now(timezone.utc)` across all modules
- **Pydantic v2:** `class Config` → `model_config = ConfigDict(...)` in all API models
- **Security:** `python-multipart` in `vector-search` bumped to `>=0.0.24` (CVE HIGH fix)

### Added
- `rct_control_plane/tests/test_formatters_dsl.py` — 42 tests for `rich_formatter.py` and `dsl_parser.py`
- `.github/workflows/release.yml` — automated GitHub Releases + PyPI publishing via OIDC
- `CODE_OF_CONDUCT.md` — Contributor Covenant
- `.github/PULL_REQUEST_TEMPLATE.md`
- `CITATION.cff`
- `.pre-commit-config.yaml`

### Changed
- CI `--cov-fail-under` raised: 20 → 70 (actual: 89%)
- Test suite: 141 → **591 passed**, 0 failures
- Coverage: 28% → **89%**
- `fastapi` bumped to `>=0.136.0`, `pydantic` to `>=2.13.1`

---

## [1.0.0-alpha] — 2026-04-13

### Added
- Initial public release of RCT Platform SDK under Apache 2.0
- Core modules: FDIA Engine, Delta Engine, Regional Adapter
- SignedAI consensus framework (S/4/6/8 tier)
- 5 reference microservices: intent-loop, analysearch-intent, vector-search, crystallizer, gateway-api
- OpenAPI 3.1.0 contract specification
- Public benchmark suite (RCT_benchmark_public)
- Whitepapers: Foundation (01) and Architecture (02)
- `rct_control_plane`: intent_schema, dsl_parser, execution_graph_ir (15 modules total)
- GitHub Actions: CI pipeline + security scanning
- CONTRIBUTING.md, SECURITY.md

---

[1.0.1a0]: https://github.com/rctlabs/rct-platform/compare/v1.0.0-alpha...v1.0.1a0
[1.0.0-alpha]: https://github.com/rctlabs/rct-platform/releases/tag/v1.0.0-alpha
