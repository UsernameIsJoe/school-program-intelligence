from school_program_intelligence.a_program import load_program_world, show_program_world


def test_load_and_show_a():
    world = load_program_world("toy_elementary")
    assert len(world.programs) >= 10
    assert len(world.relationships) >= 1
    assert len(world.schedule) >= 1
    shown = show_program_world(world)
    assert shown["component"] == "A"
    assert shown["counts"]["programs"] == len(world.programs)
