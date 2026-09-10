from __future__ import annotations

from school_program_intelligence.evaluation import compare_schemes, diagnose, evaluate_scheme
from school_program_intelligence.optimization import improve_with_cp_sat, suggest_local_improvements
from school_program_intelligence.program import load_project
from school_program_intelligence.spatial.graph import program_pair_distance


def test_load_toy_elementary():
    project = load_project("toy_elementary")
    assert project.id == "toy_elementary"
    assert len(project.programs) == 15
    assert {"A", "B"} <= set(project.scheme_map())


def test_scheme_a_passes_compliance():
    project = load_project("toy_elementary")
    report = evaluate_scheme(project, "A", fixture_name="toy_elementary")
    assert report.passed is True
    assert report.metrics["compliance.fail_count"] == 0


def test_scheme_b_fails_planted_compliance():
    project = load_project("toy_elementary")
    report = evaluate_scheme(project, "B", fixture_name="toy_elementary")
    assert report.passed is False
    assert report.metrics["compliance.fail_count"] >= 1
    # Undersized art and/or hard Grade4↔commons distance
    fail_metrics = {c.metric_id for c in report.checks if c.status == "fail"}
    assert "compliance.area" in fail_metrics or "compliance.hard_relationship" in fail_metrics


def test_scheme_a_shorter_grade5_art_travel_than_b():
    project = load_project("toy_elementary")
    d_a = program_pair_distance(project, project.get_scheme("A").assignments, "grade5_a", "art")
    d_b = program_pair_distance(project, project.get_scheme("B").assignments, "grade5_a", "art")
    assert d_a is not None and d_b is not None
    assert d_a < d_b


def test_compare_ranks_a_above_b():
    project = load_project("toy_elementary")
    result = compare_schemes(project, fixture_name="toy_elementary")
    by_id = {row["scheme_id"]: row for row in result["schemes"]}
    assert by_id["A"]["passed_compliance"] is True
    assert by_id["B"]["passed_compliance"] is False
    assert by_id["A"]["weighted_score"] > by_id["B"]["weighted_score"]


def test_diagnose_scheme_b_has_issues():
    project = load_project("toy_elementary")
    result = diagnose(project, "B", fixture_name="toy_elementary")
    assert result["issue_count"] >= 1
    assert result["issues"][0]["id"].startswith("ISSUE")


def test_local_improvement_helps_scheme_b():
    project = load_project("toy_elementary")
    result = suggest_local_improvements(project, "B", max_suggestions=5)
    assert result["suggestions"], "expected at least one improving move for planted Scheme B"
    best = result["suggestions"][0]
    assert best["delta_score"] > 0
    assert best["metrics"]["compliance.fail_count"] < result["base_fail_count"] or best[
        "metrics"
    ]["score.weighted"] > result["base_score"]


def test_cp_sat_improvement_runs():
    project = load_project("toy_elementary")
    result = improve_with_cp_sat(project, "B")
    assert "suggestions" in result
    assert result["method"] in {"cp_sat", "cp_sat_no_improve", "greedy_fallback"}
