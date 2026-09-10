from __future__ import annotations

from school_program_intelligence.engine.simulate import simulate
from school_program_intelligence.shared.models import Study, Assignment


def diagnose(study: Study, assignment: Assignment | str, fixture_name: str | None = None) -> dict:
    if isinstance(assignment, str):
        assignment = study.get_assignment(assignment)
    report = simulate(study, assignment, fixture_name=fixture_name)
    issues = []

    for check in report.checks:
        if check.status == "fail":
            issues.append(
                {
                    "severity": "high",
                    "metric_id": check.metric_id,
                    "message": check.message,
                    "evidence": {"value": check.value, "expected": check.expected},
                    "program_id": check.program_id,
                    "space_id": check.space_id,
                }
            )
        elif check.status == "warn":
            issues.append(
                {
                    "severity": "medium",
                    "metric_id": check.metric_id,
                    "message": check.message,
                    "evidence": {"value": check.value, "expected": check.expected},
                    "program_id": check.program_id,
                    "space_id": check.space_id,
                }
            )

    for pair in report.metrics.get("adjacency.pairs", []):
        if pair["penalty"] >= 0.4 and pair["importance"] in {"must_nearby", "must_touch", "should_nearby"}:
            issues.append(
                {
                    "severity": "high" if pair["importance"].startswith("must") else "medium",
                    "metric_id": "adjacency.distance",
                    "message": (
                        f"{pair['source']} → {pair['target']}: walking distance "
                        f"{pair['distance_ft']:.0f} ft vs preferred {pair['preferred_ft']} ft "
                        f"({pair['importance']})."
                    ),
                    "evidence": pair,
                }
            )

    mean_ft = report.metrics.get("travel.mean_transition_ft", 0)
    if mean_ft > 150:
        issues.append(
            {
                "severity": "medium",
                "metric_id": "travel.mean_transition_ft",
                "message": f"Mean transition distance {mean_ft:.0f} ft is above the 150 ft target.",
                "evidence": {"mean_transition_ft": mean_ft},
            }
        )

    peak = report.metrics.get("circulation.peak_load", 0)
    peak_edge = report.metrics.get("circulation.peak_edge")
    if peak >= 80:
        issues.append(
            {
                "severity": "medium",
                "metric_id": "circulation.peak_load",
                "message": f"Peak circulation load {peak:.0f} students on edge '{peak_edge}'.",
                "evidence": {
                    "peak_load": peak,
                    "peak_edge": peak_edge,
                    "edge_loads": report.metrics.get("circulation.edge_loads"),
                },
            }
        )

    for program_id, fit in report.metrics.get("spatial.fit_by_program", {}).items():
        if fit < 55:
            issues.append(
                {
                    "severity": "low",
                    "metric_id": "spatial.fit",
                    "message": f"Low spatial fit for program '{program_id}' ({fit:.0f}/100).",
                    "evidence": {"program_id": program_id, "fit": fit},
                    "program_id": program_id,
                }
            )

    # Deduplicate similar adjacency issues already covered by compliance hard fails
    numbered = []
    for i, issue in enumerate(issues, start=1):
        numbered.append({"id": f"ISSUE {i:02d}", **issue})

    return {
        "fixture": fixture_name or study.id,
        "assignment_id": assignment.id,
        "assignment_name": assignment.name,
        "issue_count": len(numbered),
        "issues": numbered,
        "metrics_snapshot": {
            "compliance.score": report.metrics["compliance.score"],
            "adjacency.score": report.metrics["adjacency.score"],
            "travel.mean_transition_ft": report.metrics["travel.mean_transition_ft"],
            "circulation.peak_load": report.metrics["circulation.peak_load"],
            "spatial.mean_fit": report.metrics["spatial.mean_fit"],
        },
    }
