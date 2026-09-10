from __future__ import annotations

from collections import defaultdict

from school_program_intelligence.shared.models import Study, Assignment
from school_program_intelligence.b_spatial.graph import (
    build_circulation_graph,
    route_path,
    space_to_node,
)


def _minutes(t: str) -> int:
    h, m = t.split(":")
    return int(h) * 60 + int(m)


def utilization_timeline(study: Study, assignment: Assignment) -> dict[str, list[dict]]:
    """Occupancy by space over schedule events."""
    reverse = {pid: sid for pid, sid in assignment.mapping.items()}
    by_space: dict[str, list[dict]] = defaultdict(list)
    for event in study.schedule:
        space_id = reverse.get(event.assigned_program)
        if not space_id:
            continue
        by_space[space_id].append(
            {
                "event_id": event.id,
                "time_start": event.time_start,
                "time_end": event.time_end,
                "students": event.students,
                "cohort": event.cohort,
                "program": event.assigned_program,
            }
        )
    return dict(by_space)


def shared_space_conflicts(study: Study, assignment: Assignment) -> list[dict]:
    timeline = utilization_timeline(study, assignment)
    conflicts = []
    for space_id, events in timeline.items():
        sorted_events = sorted(events, key=lambda e: e["time_start"])
        for i, a in enumerate(sorted_events):
            for b in sorted_events[i + 1 :]:
                if _minutes(a["time_start"]) < _minutes(b["time_end"]) and _minutes(
                    b["time_start"]
                ) < _minutes(a["time_end"]):
                    if a["program"] != b["program"]:
                        conflicts.append(
                            {
                                "space_id": space_id,
                                "a": a,
                                "b": b,
                                "students": a["students"] + b["students"],
                            }
                        )
    return conflicts


def transition_loads(study: Study, assignment: Assignment) -> dict:
    graph = build_circulation_graph(study.floor_plan)
    s2n = space_to_node(study.floor_plan)
    edge_load: dict[str, float] = defaultdict(float)
    total_student_travel = 0.0
    transition_count = 0
    transitions = []

    for event in study.schedule:
        if not event.previous_program:
            continue
        from_space = assignment.mapping.get(event.previous_program)
        to_space = assignment.mapping.get(event.assigned_program)
        if not from_space or not to_space:
            continue
        na, nb = s2n.get(from_space), s2n.get(to_space)
        if not na or not nb:
            continue
        path = route_path(graph, na, nb)
        if len(path) < 2:
            continue
        # Path length
        dist = 0.0
        for u, v in zip(path, path[1:]):
            data = graph.edges[u, v]
            dist += data["length_ft"]
            edge_id = data.get("id", f"{u}-{v}")
            edge_load[edge_id] += event.students
        total_student_travel += dist * event.students
        transition_count += 1
        transitions.append(
            {
                "event_id": event.id,
                "from_program": event.previous_program,
                "to_program": event.assigned_program,
                "students": event.students,
                "distance_ft": dist,
                "path_nodes": path,
            }
        )

    peak_edge = max(edge_load.items(), key=lambda x: x[1]) if edge_load else ("none", 0.0)
    mean_transition = (
        sum(t["distance_ft"] for t in transitions) / len(transitions) if transitions else 0.0
    )
    return {
        "travel.total_student_ft": round(total_student_travel, 1),
        "travel.mean_transition_ft": round(mean_transition, 1),
        "travel.transition_count": transition_count,
        "circulation.peak_edge": peak_edge[0],
        "circulation.peak_load": peak_edge[1],
        "circulation.edge_loads": dict(edge_load),
        "circulation.transitions": transitions,
        "utilization.by_space": utilization_timeline(study, assignment),
        "utilization.conflicts": shared_space_conflicts(study, assignment),
    }
