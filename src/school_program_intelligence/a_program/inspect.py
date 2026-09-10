from __future__ import annotations

from school_program_intelligence.shared.models import ProgramWorld


def show_program_world(world: ProgramWorld) -> dict:
    return {
        "component": "A",
        "id": world.id,
        "name": world.name,
        "counts": {
            "programs": len(world.programs),
            "relationships": len(world.relationships),
            "schedule_events": len(world.schedule),
            "activities": len(world.activities),
        },
        "programs": [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "area_target": p.area_target,
                "capacity": p.capacity,
            }
            for p in world.programs
        ],
        "relationships": [
            {
                "source": r.source_program,
                "target": r.target_program,
                "importance": r.importance.value,
                "preferred_distance_ft": r.preferred_distance_ft,
                "hard": r.hard,
            }
            for r in world.relationships
        ],
        "schedule": [
            {
                "id": e.id,
                "time_start": e.time_start,
                "time_end": e.time_end,
                "program": e.assigned_program,
                "cohort": e.cohort,
                "students": e.students,
            }
            for e in world.schedule
        ],
    }
