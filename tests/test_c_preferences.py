from school_program_intelligence.c_preferences import interpret_priorities, load_preferences


def test_load_preferences_and_interpret():
    prefs = load_preferences("toy_elementary")
    assert prefs.prompt
    assert prefs.weights.student_travel > 0
    result = interpret_priorities(
        "We care most about minimizing student travel and grade neighborhoods. "
        "Willing to accept lower area efficiency.",
        base=prefs.weights,
    )
    assert result.levels["student_travel"] == "high"
    assert result.levels["neighborhood_cohesion"] == "high"
    assert result.levels["area_efficiency"] == "low"
    assert result.weights.student_travel > result.weights.area_efficiency
