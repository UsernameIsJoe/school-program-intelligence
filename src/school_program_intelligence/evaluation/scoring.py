from __future__ import annotations

from school_program_intelligence.evaluation.adjacency import adjacency_metrics
from school_program_intelligence.evaluation.capacity import evaluate_compliance
from school_program_intelligence.program.schema import EvaluationReport, Project, Scheme
from school_program_intelligence.spatial.graph import all_program_distances
from school_program_intelligence.spatial.space_syntax import spatial_fit, spatial_fingerprints
from school_program_intelligence.temporal.operations import transition_loads


def evaluate_scheme(project: Project, scheme: Scheme | str, fixture_name: str | None = None) -> EvaluationReport:
    if isinstance(scheme, str):
        scheme = project.get_scheme(scheme)

    distances = all_program_distances(project, scheme.assignments)
    compliance = evaluate_compliance(project, scheme, distances=distances)
    adj = adjacency_metrics(project, scheme)
    temporal = transition_loads(project, scheme)
    fits = spatial_fit(project, scheme.assignments)
    fps = spatial_fingerprints(project)

    mean_fit = sum(fits.values()) / len(fits) if fits else 0.0
    conflict_count = len(temporal["utilization.conflicts"])

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
        "utilization.conflict_count": conflict_count,
        "utilization.conflicts": temporal["utilization.conflicts"],
        "utilization.by_space": temporal["utilization.by_space"],
        "spatial.mean_fit": round(mean_fit, 2),
        "spatial.fit_by_program": {k: round(v, 2) for k, v in fits.items()},
        "spatial.fingerprints": fps,
        "priorities": project.priorities.model_dump(),
    }

    # Composite for sorting — not a black-box AI score; weighted explicit metrics
    p = project.priorities
    travel_norm = max(0.0, 100.0 - temporal["travel.mean_transition_ft"] / 5.0)
    circ_norm = max(0.0, 100.0 - float(temporal["circulation.peak_load"]) / 2.0)
    composite = (
        p.capacity_fit * metrics["compliance.score"]
        + p.adjacency_fit * metrics["adjacency.score"]
        + p.student_travel * travel_norm
        + p.circulation_stress * circ_norm
        + p.shared_space_performance * mean_fit
    ) / (
        p.capacity_fit
        + p.adjacency_fit
        + p.student_travel
        + p.circulation_stress
        + p.shared_space_performance
    )
    metrics["score.weighted"] = round(composite, 2)

    return EvaluationReport(
        fixture=fixture_name or project.id,
        scheme_id=scheme.id,
        scheme_name=scheme.name,
        checks=compliance.checks,
        metrics=metrics,
        passed=compliance.passed,
    )


def compare_schemes(project: Project, fixture_name: str | None = None) -> dict:
    rows = []
    for scheme in project.schemes:
        report = evaluate_scheme(project, scheme, fixture_name=fixture_name)
        rows.append(
            {
                "scheme_id": scheme.id,
                "scheme_name": scheme.name,
                "passed_compliance": report.passed,
                "compliance_score": report.metrics["compliance.score"],
                "adjacency_score": report.metrics["adjacency.score"],
                "mean_transition_ft": report.metrics["travel.mean_transition_ft"],
                "total_student_travel_ft": report.metrics["travel.total_student_ft"],
                "peak_circulation_load": report.metrics["circulation.peak_load"],
                "peak_edge": report.metrics["circulation.peak_edge"],
                "spatial_mean_fit": report.metrics["spatial.mean_fit"],
                "weighted_score": report.metrics["score.weighted"],
                "fail_count": report.metrics["compliance.fail_count"],
            }
        )
    rows.sort(key=lambda r: (-r["passed_compliance"], -r["weighted_score"]))
    return {"fixture": fixture_name or project.id, "schemes": rows}
