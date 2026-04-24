"""
Tests for rct_control_plane.intent_templates — RefactorTemplate + BuildAppTemplate.

Covers:
- Template matching (confidence score)
- Plan generation (phases, cost, duration)
- DSL output generation
- Scope and complexity scaling
- Approval logic
"""
from __future__ import annotations

from decimal import Decimal

from rct_control_plane.intent_schema import (
    ContextBundle,
    IntentObject,
    IntentPriority,
    IntentType,
    RiskProfile,
    ScopeObject,
    ScopeType,
)
from rct_control_plane.intent_templates.refactor_template import (
    RefactorTemplate,
    RefactoringPlan,
)
from rct_control_plane.intent_templates.build_app_template import (
    BuildAppTemplate,
    BuildPlan,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _context(tier: str = "PRO") -> ContextBundle:
    return ContextBundle(user_id="test-user", user_tier=tier)


def _scope(scope_type: ScopeType = ScopeType.MODULE, target: str = "mymodule") -> ScopeObject:
    return ScopeObject(scope_type=scope_type, target=target)


def _intent(
    goal: str = "Refactor the module to follow SOLID principles",
    intent_type: IntentType = IntentType.REFACTOR,
    scope_type: ScopeType = ScopeType.MODULE,
    risk: RiskProfile = RiskProfile.LOW,
    priority: IntentPriority = IntentPriority.MEDIUM,
) -> IntentObject:
    return IntentObject(
        goal=goal,
        intent_type=intent_type,
        scope=_scope(scope_type),
        context=_context(),
        risk_profile=risk,
        priority=priority,
    )


# ===========================================================================
# TestRefactorTemplateMatch
# ===========================================================================

class TestRefactorTemplateMatch:
    def setup_method(self):
        self.template = RefactorTemplate()

    def test_match_refactor_intent_high_confidence(self):
        intent = _intent(goal="Refactor module using clean architecture patterns")
        score = self.template.match(intent)
        assert score >= 0.7

    def test_match_non_refactor_intent_low_confidence(self):
        intent = _intent(
            goal="Build a new FastAPI microservice",
            intent_type=IntentType.BUILD_APP,
        )
        score = self.template.match(intent)
        assert score < 0.5

    def test_match_score_in_range(self):
        intent = _intent()
        score = self.template.match(intent)
        assert 0.0 <= score <= 1.0

    def test_match_keyword_boost(self):
        base_intent = _intent(goal="Refactor module")
        keyword_intent = _intent(goal="Refactor module using clean architecture SOLID DRY patterns")
        base_score = self.template.match(base_intent)
        kw_score = self.template.match(keyword_intent)
        assert kw_score >= base_score

    def test_match_module_scope_counts(self):
        intent = _intent(scope_type=ScopeType.MODULE)
        score = self.template.match(intent)
        assert score > 0.0


# ===========================================================================
# TestRefactorTemplatePlan
# ===========================================================================

class TestRefactorTemplatePlan:
    def setup_method(self):
        self.template = RefactorTemplate()

    def test_plan_returns_refactoring_plan(self):
        intent = _intent()
        plan = self.template.to_plan(intent)
        assert isinstance(plan, RefactoringPlan)

    def test_plan_low_risk_has_no_simulate_phase(self):
        intent = _intent(risk=RiskProfile.LOW)
        plan = self.template.to_plan(intent)
        phase_names = [p.name for p in plan.phases]
        assert "simulate" not in phase_names

    def test_plan_structural_risk_has_simulate_phase(self):
        intent = _intent(risk=RiskProfile.STRUCTURAL)
        plan = self.template.to_plan(intent)
        phase_names = [p.name for p in plan.phases]
        assert "simulate" in phase_names

    def test_plan_systemic_risk_has_simulate_phase(self):
        intent = _intent(risk=RiskProfile.SYSTEMIC)
        plan = self.template.to_plan(intent)
        phase_names = [p.name for p in plan.phases]
        assert "simulate" in phase_names

    def test_plan_always_has_analyze_plan_transform_validate(self):
        intent = _intent()
        plan = self.template.to_plan(intent)
        phase_names = [p.name for p in plan.phases]
        for required in ["analyze", "plan", "transform", "validate"]:
            assert required in phase_names

    def test_plan_total_cost_positive(self):
        intent = _intent()
        plan = self.template.to_plan(intent)
        assert plan.total_estimated_cost > Decimal("0")

    def test_plan_total_duration_positive(self):
        intent = _intent()
        plan = self.template.to_plan(intent)
        assert plan.total_estimated_duration_seconds > 0

    def test_plan_total_cost_equals_sum_of_phases(self):
        intent = _intent()
        plan = self.template.to_plan(intent)
        phase_sum = sum(p.estimated_cost for p in plan.phases)
        assert abs(plan.total_estimated_cost - phase_sum) < Decimal("0.001")

    def test_plan_systemic_requires_approval(self):
        intent = _intent(risk=RiskProfile.SYSTEMIC)
        plan = self.template.to_plan(intent)
        assert plan.requires_approval is True

    def test_plan_low_risk_does_not_require_approval_unless_high_cost(self):
        intent = _intent(risk=RiskProfile.LOW, scope_type=ScopeType.FILE)
        plan = self.template.to_plan(intent)
        # Low risk + file scope → small cost → no approval needed
        if plan.total_estimated_cost <= Decimal("2.00"):
            assert plan.requires_approval is False

    def test_plan_repository_scope_costs_more_than_file_scope(self):
        file_intent = _intent(scope_type=ScopeType.FILE)
        repo_intent = _intent(scope_type=ScopeType.REPOSITORY)
        file_cost = self.template.estimate_cost(file_intent)
        repo_cost = self.template.estimate_cost(repo_intent)
        assert repo_cost > file_cost

    def test_plan_repository_scope_takes_longer_than_file_scope(self):
        file_intent = _intent(scope_type=ScopeType.FILE)
        repo_intent = _intent(scope_type=ScopeType.REPOSITORY)
        file_dur = self.template.estimate_duration(file_intent)
        repo_dur = self.template.estimate_duration(repo_intent)
        assert repo_dur > file_dur

    def test_plan_has_correct_intent_id(self):
        intent = _intent()
        plan = self.template.to_plan(intent)
        assert plan.intent_id == str(intent.id)

    def test_plan_risk_level_matches_intent(self):
        intent = _intent(risk=RiskProfile.STRUCTURAL)
        plan = self.template.to_plan(intent)
        # risk_level stored as string after use_enum_values
        assert "STRUCTURAL" in str(plan.risk_level).upper()


# ===========================================================================
# TestRefactorTemplateDSL
# ===========================================================================

class TestRefactorTemplateDSL:
    def setup_method(self):
        self.template = RefactorTemplate()

    def test_to_dsl_returns_string(self):
        intent = _intent()
        plan = self.template.to_plan(intent)
        dsl = self.template.to_dsl(plan)
        assert isinstance(dsl, str)
        assert len(dsl) > 0

    def test_to_dsl_contains_intent_block(self):
        intent = _intent()
        plan = self.template.to_plan(intent)
        dsl = self.template.to_dsl(plan)
        assert "intent" in dsl
        assert "refactor_" in dsl

    def test_to_dsl_contains_phase_blocks(self):
        intent = _intent()
        plan = self.template.to_plan(intent)
        dsl = self.template.to_dsl(plan)
        assert "phase analyze" in dsl
        assert "phase transform" in dsl

    def test_to_dsl_contains_depends_on(self):
        intent = _intent()
        plan = self.template.to_plan(intent)
        dsl = self.template.to_dsl(plan)
        assert "depends_on" in dsl

    def test_estimate_cost_matches_plan(self):
        intent = _intent()
        direct_cost = self.template.estimate_cost(intent)
        plan = self.template.to_plan(intent)
        assert direct_cost == plan.total_estimated_cost

    def test_estimate_duration_matches_plan(self):
        intent = _intent()
        direct_dur = self.template.estimate_duration(intent)
        plan = self.template.to_plan(intent)
        assert direct_dur == plan.total_estimated_duration_seconds


# ===========================================================================
# TestBuildAppTemplateMatch
# ===========================================================================

class TestBuildAppTemplateMatch:
    def setup_method(self):
        self.template = BuildAppTemplate()

    def test_match_build_app_intent_high_confidence(self):
        intent = _intent(
            goal="Build a new FastAPI REST API service",
            intent_type=IntentType.BUILD_APP,
        )
        score = self.template.match(intent)
        assert score >= 0.7

    def test_match_refactor_intent_low_confidence(self):
        intent = _intent(goal="Refactor the module", intent_type=IntentType.REFACTOR)
        score = self.template.match(intent)
        # Build template gives low confidence for refactor intent type
        assert score < 0.5

    def test_match_score_in_range(self):
        intent = _intent(intent_type=IntentType.BUILD_APP)
        score = self.template.match(intent)
        assert 0.0 <= score <= 1.0

    def test_match_with_build_keywords(self):
        intent = _intent(goal="Build a new web app scaffold", intent_type=IntentType.BUILD_APP)
        score = self.template.match(intent)
        assert score >= 0.7


# ===========================================================================
# TestBuildAppTemplatePlan
# ===========================================================================

class TestBuildAppTemplatePlan:
    def setup_method(self):
        self.template = BuildAppTemplate()

    def test_plan_returns_build_plan(self):
        intent = _intent(intent_type=IntentType.BUILD_APP)
        plan = self.template.to_plan(intent)
        assert isinstance(plan, BuildPlan)

    def test_plan_has_5_phases(self):
        intent = _intent(intent_type=IntentType.BUILD_APP)
        plan = self.template.to_plan(intent)
        assert len(plan.phases) == 5

    def test_plan_phase_names_correct(self):
        intent = _intent(intent_type=IntentType.BUILD_APP)
        plan = self.template.to_plan(intent)
        phase_names = [p.name for p in plan.phases]
        for required in ["requirements", "architecture", "scaffolding", "implementation", "configuration"]:
            assert required in phase_names

    def test_plan_detects_api_app_type(self):
        intent = _intent(
            goal="Build a REST API backend with FastAPI",
            intent_type=IntentType.BUILD_APP,
        )
        plan = self.template.to_plan(intent)
        assert plan.app_type == "api"

    def test_plan_detects_web_app_type(self):
        intent = _intent(
            goal="Build a new web dashboard UI",
            intent_type=IntentType.BUILD_APP,
        )
        plan = self.template.to_plan(intent)
        assert plan.app_type == "web"

    def test_plan_detects_cli_app_type(self):
        intent = _intent(
            goal="Build a CLI tool for deployment",
            intent_type=IntentType.BUILD_APP,
        )
        plan = self.template.to_plan(intent)
        assert plan.app_type == "cli"

    def test_plan_default_app_type_generic(self):
        intent = _intent(
            goal="Build something completely new",
            intent_type=IntentType.BUILD_APP,
        )
        plan = self.template.to_plan(intent)
        assert plan.app_type in ("generic", "api", "web")  # defaults allowed

    def test_plan_detects_python_stack(self):
        intent = _intent(
            goal="Build a FastAPI Python service",
            intent_type=IntentType.BUILD_APP,
        )
        plan = self.template.to_plan(intent)
        assert "python" in plan.tech_stack

    def test_plan_detects_typescript_stack(self):
        intent = _intent(
            goal="Build a TypeScript Next.js application",
            intent_type=IntentType.BUILD_APP,
        )
        plan = self.template.to_plan(intent)
        assert "typescript" in plan.tech_stack or "javascript" in plan.tech_stack

    def test_plan_has_artifacts(self):
        intent = _intent(intent_type=IntentType.BUILD_APP)
        plan = self.template.to_plan(intent)
        assert len(plan.artifacts) > 0

    def test_plan_total_cost_positive(self):
        intent = _intent(intent_type=IntentType.BUILD_APP)
        plan = self.template.to_plan(intent)
        assert plan.total_estimated_cost > Decimal("0")

    def test_plan_total_duration_positive(self):
        intent = _intent(intent_type=IntentType.BUILD_APP)
        plan = self.template.to_plan(intent)
        assert plan.total_estimated_duration_seconds > 0

    def test_plan_repository_scope_higher_cost(self):
        file_intent = _intent(intent_type=IntentType.BUILD_APP, scope_type=ScopeType.FILE)
        repo_intent = _intent(intent_type=IntentType.BUILD_APP, scope_type=ScopeType.REPOSITORY)
        assert self.template.estimate_cost(repo_intent) > self.template.estimate_cost(file_intent)

    def test_plan_has_correct_intent_id(self):
        intent = _intent(intent_type=IntentType.BUILD_APP)
        plan = self.template.to_plan(intent)
        assert plan.intent_id == str(intent.id)

    def test_plan_metadata_contains_complexity(self):
        intent = _intent(intent_type=IntentType.BUILD_APP)
        plan = self.template.to_plan(intent)
        assert "complexity" in plan.metadata


# ===========================================================================
# TestBuildAppTemplateDSL
# ===========================================================================

class TestBuildAppTemplateDSL:
    def setup_method(self):
        self.template = BuildAppTemplate()

    def test_to_dsl_returns_string(self):
        intent = _intent(intent_type=IntentType.BUILD_APP)
        plan = self.template.to_plan(intent)
        dsl = self.template.to_dsl(plan)
        assert isinstance(dsl, str)
        assert len(dsl) > 0

    def test_to_dsl_contains_intent_block(self):
        intent = _intent(intent_type=IntentType.BUILD_APP)
        plan = self.template.to_plan(intent)
        dsl = self.template.to_dsl(plan)
        assert "intent" in dsl
        assert "build_app_" in dsl

    def test_to_dsl_contains_phase_scaffolding(self):
        intent = _intent(intent_type=IntentType.BUILD_APP)
        plan = self.template.to_plan(intent)
        dsl = self.template.to_dsl(plan)
        assert "scaffolding" in dsl

    def test_estimate_cost_shortcut(self):
        intent = _intent(intent_type=IntentType.BUILD_APP)
        cost = self.template.estimate_cost(intent)
        assert isinstance(cost, Decimal)
        assert cost > Decimal("0")

    def test_estimate_duration_shortcut(self):
        intent = _intent(intent_type=IntentType.BUILD_APP)
        dur = self.template.estimate_duration(intent)
        assert isinstance(dur, int)
        assert dur > 0


# ===========================================================================
# TestTemplatesInit
# ===========================================================================

class TestTemplatesInit:
    def test_templates_init_exports(self):
        from rct_control_plane.intent_templates import __init__ as tmpl_init
        # Should be importable without error
        assert tmpl_init is not None

    def test_refactor_template_all_export(self):
        from rct_control_plane.intent_templates.refactor_template import __all__
        assert "RefactorTemplate" in __all__

    def test_build_app_template_all_export(self):
        from rct_control_plane.intent_templates.build_app_template import __all__
        assert "BuildAppTemplate" in __all__
