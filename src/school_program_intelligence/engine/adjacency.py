from __future__ import annotations

from school_program_intelligence.shared.models import Importance, Study, Assignment
from school_program_intelligence.b_spatial.graph import program_pair_distance


IMPORTANCE_WEIGHT = {
    Importance.MUST_TOUCH: 5.0,
    Importance.MUST_NEARBY: 4.0,
    Importance.SHOULD_NEARBY: 2.5,
    Importance.WEAK: 1.0,
    Importance.NEUTRAL: 0.0,
    Importance.SHOULD_SEPARATE: 2.0,
}


def penalty_curve(distance: float, preferred: float | None, importance: Importance) -> float:
    if importance == Importance.NEUTRAL:
        return 0.0
    if preferred is None:
        preferred = 100.0
    if importance == Importance.SHOULD_SEPARATE:
        # Penalize being too close
        if distance >= preferred:
            return 0.0
        return (preferred - distance) / preferred
    # Closer is better
    if distance <= preferred:
        return 0.0
    return (distance - preferred) / preferred


def adjacency_metrics(study: Study, assignment: Assignment) -> dict:
    pairs = []
    total_penalty = 0.0
    weight_sum = 0.0
    for rel in study.relationships:
        dist = program_pair_distance(
            study, assignment.mapping, rel.source_program, rel.target_program
        )
        w = IMPORTANCE_WEIGHT[rel.importance]
        if dist is None:
            pen = 1.0
            dist_val = None
        else:
            pen = penalty_curve(dist, rel.preferred_distance_ft, rel.importance)
            dist_val = dist
        weighted = w * pen
        total_penalty += weighted
        weight_sum += w
        pairs.append(
            {
                "source": rel.source_program,
                "target": rel.target_program,
                "importance": rel.importance.value,
                "distance_ft": dist_val,
                "preferred_ft": rel.preferred_distance_ft,
                "penalty": round(pen, 3),
                "weighted_penalty": round(weighted, 3),
            }
        )
    score = 100.0 * (1.0 - total_penalty / weight_sum) if weight_sum else 100.0
    return {
        "adjacency.penalty": round(total_penalty, 3),
        "adjacency.score": round(max(0.0, score), 2),
        "adjacency.pairs": pairs,
    }
