from school_program_intelligence.llm import interpret_priorities
from school_program_intelligence.program import load_project
from school_program_intelligence.web.viz import bubble_diagram, plan_overlays
from school_program_intelligence.evaluation import diagnose, evaluate_scheme
from school_program_intelligence.optimization import suggest_local_improvements


def test_priority_prompt_boosts_travel_and_neighborhood():
    text = (
        "We care most about maintaining grade neighborhoods and minimizing student travel. "
        "We are willing to accept slightly less area efficiency."
    )
    result = interpret_priorities(text)
    assert result.levels["student_travel"] == "high"
    assert result.levels["neighborhood_cohesion"] == "high"
    assert result.levels["area_efficiency"] == "low"
    assert result.weights.student_travel > result.weights.area_efficiency


def test_bubble_and_plan_overlays_for_scheme_b():
    project = load_project("toy_elementary")
    scheme = project.get_scheme("B")
    report = evaluate_scheme(project, scheme)
    issues = diagnose(project, scheme)
    bubbles = bubble_diagram(project, scheme, report.metrics["adjacency.pairs"])
    assert len(bubbles["nodes"]) >= 10
    assert len(bubbles["edges"]) >= 1

    improvements = suggest_local_improvements(project, scheme, max_suggestions=1)
    suggestion = improvements["suggestions"][0] if improvements["suggestions"] else None
    plan = plan_overlays(project, scheme, issues["issues"], suggestion=suggestion)
    roles = {p["role"] for p in plan}
    assert "issue_high" in roles or "issue_medium" in roles
    if suggestion:
        assert "suggest_from" in roles and "suggest_to" in roles
