from school_program_intelligence.c_preferences import PriorityWeights, interpret_priorities
from school_program_intelligence.engine import simulate
from school_program_intelligence.rating import score_report
from school_program_intelligence.shared import load_study


def test_rating_scores_engine_metrics():
    study = load_study("toy_elementary")
    report = simulate(study, "A")
    scored = score_report(report, study.preferences.weights)
    assert "weighted_score" in scored
    assert scored["assignment_id"] == "A"
    assert len(scored["parts"]) >= 5


def test_rating_travel_weight_changes_relative_order():
    study = load_study("toy_elementary")
    a = simulate(study, "A")
    b = simulate(study, "B")
    travel_heavy = PriorityWeights(
        student_travel=1.0,
        neighborhood_cohesion=0.1,
        shared_space_performance=0.1,
        area_efficiency=0.1,
        capacity_fit=0.2,
        adjacency_fit=0.2,
        circulation_stress=0.1,
    )
    sa = score_report(a, travel_heavy)["weighted_score"]
    sb = score_report(b, travel_heavy)["weighted_score"]
    # A has shorter mean travel; under travel-heavy weights should beat B
    assert a.metrics["travel.mean_transition_ft"] < b.metrics["travel.mean_transition_ft"]
    assert sa > sb
