"""Rating — apply C preference weights to engine metrics.

Does not invent metrics. Does not search.
"""

from __future__ import annotations

from school_program_intelligence.shared.models import PriorityWeights, SimulationReport


def score_report(report: SimulationReport, weights: PriorityWeights) -> dict:
    m = report.metrics
    travel_norm = max(0.0, 100.0 - float(m.get("travel.mean_transition_ft", 0)) / 5.0)
    circ_norm = max(0.0, 100.0 - float(m.get("circulation.peak_load", 0)) / 2.0)
    mean_fit = float(m.get("spatial.mean_fit", 0))
    area_norm = float(m.get("compliance.score", 0))
    neighborhood = float(m.get("adjacency.score", 0))
    parts = [
        ("capacity_fit", weights.capacity_fit, float(m.get("compliance.score", 0))),
        ("adjacency_fit", weights.adjacency_fit, float(m.get("adjacency.score", 0))),
        ("neighborhood_cohesion", weights.neighborhood_cohesion, neighborhood),
        ("student_travel", weights.student_travel, travel_norm),
        ("circulation_stress", weights.circulation_stress, circ_norm),
        ("shared_space_performance", weights.shared_space_performance, mean_fit),
        ("area_efficiency", weights.area_efficiency, area_norm),
    ]
    num = sum(w * v for _, w, v in parts)
    den = sum(w for _, w, _ in parts) or 1.0
    weighted = round(num / den, 2)
    return {
        "weighted_score": weighted,
        "weights": weights.model_dump(),
        "parts": [
            {"metric": name, "weight": w, "value": round(v, 2), "contribution": round(w * v, 2)}
            for name, w, v in parts
        ],
        "assignment_id": report.assignment_id,
        "passed": report.passed,
    }
