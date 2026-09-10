from __future__ import annotations

import re
from dataclasses import dataclass

from school_program_intelligence.shared.models import PriorityWeights

# Map natural-language cues → PriorityWeights fields.
# Levels: high=1.0, medium=0.55, low=0.2 (editable after interpretation).
_LEVEL = {"high": 1.0, "medium": 0.55, "low": 0.2}

_METRIC_CUES: list[tuple[str, tuple[str, ...]]] = [
    (
        "student_travel",
        (
            r"student\s+travel",
            r"walking\s+distance",
            r"minimize\s+travel",
            r"less\s+travel",
            r"travel\s+time",
            r"transitions?",
            r"circulation\s+distance",
        ),
    ),
    (
        "neighborhood_cohesion",
        (
            r"neighborhood",
            r"grade\s+cluster",
            r"keep\s+(?:grades?|cohorts?)\s+together",
            r"small\s+learning",
            r"cohesion",
        ),
    ),
    (
        "shared_space_performance",
        (
            r"shared\s+space",
            r"learning\s+commons",
            r"breakout",
            r"commons",
            r"flexible\s+learning",
        ),
    ),
    (
        "area_efficiency",
        (
            r"area\s+efficiency",
            r"compact\s+area",
            r"minimize\s+area",
            r"sf\b",
            r"square\s+feet",
            r"construction\s+(?:cost|efficiency)",
        ),
    ),
    (
        "capacity_fit",
        (
            r"capacity",
            r"overcrowd",
            r"room\s+size",
            r"fit\s+the\s+program",
            r"program\s+fit",
        ),
    ),
    (
        "adjacency_fit",
        (
            r"adjacenc",
            r"near(?:by)?",
            r"proximity",
            r"next\s+to",
            r"relationship",
        ),
    ),
    (
        "circulation_stress",
        (
            r"bottleneck",
            r"congestion",
            r"corridor\s+load",
            r"peak\s+(?:load|traffic)",
            r"stair\s+load",
            r"crowding",
        ),
    ),
]

_HIGH = re.compile(
    r"\b(?:most|highest|critical|must|priority|care\s+most|especially|"
    r"very\s+important|high(?:ly)?|primary)\b",
    re.I,
)
_LOW = re.compile(
    r"\b(?:less|lower|willing\s+to\s+accept|trade[\s-]?off|not\s+as|"
    r"secondary|low(?:er)?|minor|optional)\b",
    re.I,
)


@dataclass
class PriorityInterpretation:
    prompt: str
    weights: PriorityWeights
    levels: dict[str, str]
    notes: list[str]


def _sentence_level(sentence: str) -> str:
    if _HIGH.search(sentence) and not _LOW.search(sentence):
        return "high"
    if _LOW.search(sentence):
        return "low"
    return "medium"


def interpret_priorities(prompt: str, base: PriorityWeights | None = None) -> PriorityInterpretation:
    """Translate a natural-language priority statement into visible editable weights.

    Deterministic cue matching — not an LLM. Engines still do all scoring.
    """
    text = (prompt or "").strip()
    weights = (base or PriorityWeights()).model_copy(deep=True)
    levels = {k: "medium" for k in PriorityWeights.model_fields}
    notes: list[str] = []

    if not text:
        notes.append("No prompt provided; using default / fixture weights.")
        return PriorityInterpretation(prompt=text, weights=weights, levels=levels, notes=notes)

    # Split into clauses so "care most about X, willing to accept Y" scopes correctly.
    clauses = re.split(r"[.;\n]+|(?:,\s*(?:and|but|while)\s+)", text)
    touched: set[str] = set()

    for clause in clauses:
        clause = clause.strip()
        if not clause:
            continue
        level = _sentence_level(clause)
        for field, patterns in _METRIC_CUES:
            if any(re.search(p, clause, flags=re.I) for p in patterns):
                levels[field] = level
                setattr(weights, field, _LEVEL[level])
                touched.add(field)
                notes.append(f"{field} ← {level} (from “{clause[:80]}”)")

    # Global "care most about A and B" without per-clause lows: boost matched, leave rest.
    if not touched:
        notes.append("No metric cues recognized; weights left unchanged. Edit sliders or rephrase.")
    else:
        # Soft-down unmentioned metrics so stated priorities dominate the weighted score.
        for field in PriorityWeights.model_fields:
            if field not in touched and levels[field] == "medium":
                levels[field] = "medium"
                # leave numeric weight as base/default

    return PriorityInterpretation(prompt=text, weights=weights, levels=levels, notes=notes)


def weights_from_levels(levels: dict[str, str], base: PriorityWeights | None = None) -> PriorityWeights:
    weights = (base or PriorityWeights()).model_copy(deep=True)
    for field, level in levels.items():
        if field in PriorityWeights.model_fields and level in _LEVEL:
            setattr(weights, field, _LEVEL[level])
    return weights
