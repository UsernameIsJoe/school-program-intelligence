"""Engine — simulate one assignment against A + B.

Produces measured metrics only. Does not apply preference weights (that is rating).
Does not search or generate alternatives.
"""

from __future__ import annotations

from school_program_intelligence.b_spatial.graph import all_program_distances
from school_program_intelligence.b_spatial.space_syntax import spatial_fit, spatial_fingerprints
from school_program_intelligence.engine.adjacency import adjacency_metrics
from school_program_intelligence.engine.capacity import evaluate_compliance
from school_program_intelligence.engine.temporal import transition_loads
from school_program_intelligence.shared.models import Assignment, SimulationReport, Study


def simulate(
    study: Study,
    assignment: Assignment | str,
    fixture_name: str | None = None,
) -> SimulationReport:
    if isinstance(assignment, str):
        assignment = study.get_assignment(assignment)

    distances = all_program_distances(study, assignment.mapping)
    compliance = evaluate_compliance(study, assignment, distances=distances)
    adj = adjacency_metrics(study, assignment)
    temporal = transition_loads(study, assignment)
    fits = spatial_fit(study, assignment.mapping)
    fps = spatial_fingerprints(study)
    mean_fit = sum(fits.values()) / len(fits) if fits else 0.0

    metrics = {
        **compliance.metrics,
        **{k: v for k, v in adj.items() if k != "adjacency.pairs"},
        "adjacency.pairs": adj["adjacency.pairs"],
        "travel.total_student_ft": temporal["travel.total_student_ft"],
        "travel.mean_transition_ft": temporal["travel.mean_transition_ft"],
        "travel.transition_count": temporal["travel.transition_count"],
        "circulation.peak_edge": temporal["circulation.peak_edge"],
        "circulation.peak_load": temporal["circulation.peak_load"],
        "circulation.edge_loads": temporal["circulation.edge_loads"],
        "utilization.conflict_count": len(temporal["utilization.conflicts"]),
        "utilization.conflicts": temporal["utilization.conflicts"],
        "utilization.by_space": temporal["utilization.by_space"],
        "spatial.mean_fit": round(mean_fit, 2),
        "spatial.fit_by_program": {k: round(v, 2) for k, v in fits.items()},
        "spatial.fingerprints": fps,
    }

    return SimulationReport(
        fixture=fixture_name or study.id,
        assignment_id=assignment.id,
        assignment_name=assignment.name,
        checks=compliance.checks,
        metrics=metrics,
        passed=compliance.passed,
    )
