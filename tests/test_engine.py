from school_program_intelligence.engine import diagnose, simulate
from school_program_intelligence.shared import load_study


def test_engine_simulate_assignment_a_passes():
    study = load_study("toy_elementary")
    report = simulate(study, "A", fixture_name="toy_elementary")
    assert report.passed is True
    assert report.metrics["compliance.fail_count"] == 0
    assert "travel.mean_transition_ft" in report.metrics
    assert "adjacency.score" in report.metrics
    # Engine does not apply C ranking
    assert "score.weighted" not in report.metrics


def test_engine_simulate_assignment_b_fails():
    study = load_study("toy_elementary")
    report = simulate(study, "B", fixture_name="toy_elementary")
    assert report.passed is False
    issues = diagnose(study, "B", fixture_name="toy_elementary")
    assert issues["issue_count"] >= 1
