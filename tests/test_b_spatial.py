from school_program_intelligence.b_spatial import (
    build_circulation_graph,
    load_spatial_field,
    show_spatial_field,
)


def test_load_and_show_b():
    field = load_spatial_field("toy_elementary")
    assert len(field.floor_plan.spaces) >= 10
    graph = build_circulation_graph(field.floor_plan)
    assert graph.number_of_nodes() >= 5
    shown = show_spatial_field(field)
    assert shown["component"] == "B"
    assert shown["counts"]["assignable"] >= 1
