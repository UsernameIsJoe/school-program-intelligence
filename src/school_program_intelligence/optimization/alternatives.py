from __future__ import annotations

from school_program_intelligence.evaluation.scoring import evaluate_scheme
from school_program_intelligence.program.schema import Project, Scheme


def _candidate_spaces(project: Project) -> list[str]:
    return [
        s.id
        for s in project.floor_plan.spaces
        if not s.is_circulation and s.space_type not in {"stair", "corridor"}
    ]


def _score(project: Project, assignments: dict[str, str]) -> float:
    scheme = Scheme(id="tmp", name="tmp", assignments=assignments)
    report = evaluate_scheme(project, scheme)
    # Prefer compliance + weighted score
    bonus = 50.0 if report.passed else 0.0
    return report.metrics["score.weighted"] + bonus - 5.0 * report.metrics["compliance.fail_count"]


def suggest_local_improvements(
    project: Project,
    scheme: Scheme | str,
    max_suggestions: int = 5,
) -> dict:
    if isinstance(scheme, str):
        scheme = project.get_scheme(scheme)

    base_assignments = dict(scheme.assignments)
    base_score = _score(project, base_assignments)
    base_report = evaluate_scheme(project, scheme)

    occupied = set(base_assignments.values())
    programs = list(base_assignments.keys())
    candidates = _candidate_spaces(project)

    suggestions: list[dict] = []

    # Operator 1: swap two programs
    for i, a in enumerate(programs):
        for b in programs[i + 1 :]:
            trial = dict(base_assignments)
            trial[a], trial[b] = trial[b], trial[a]
            score = _score(project, trial)
            if score > base_score + 0.5:
                suggestions.append(
                    {
                        "operator": "swap",
                        "description": f"Swap {a} and {b}",
                        "delta_score": round(score - base_score, 2),
                        "assignments": trial,
                        "score": round(score, 2),
                    }
                )

    # Operator 2: move a program to an unoccupied candidate space
    free = [c for c in candidates if c not in occupied]
    movable = ["art", "learning_commons", "music", "sped", "teacher_planning"]
    for program_id in movable:
        if program_id not in base_assignments:
            continue
        for space_id in free + [
            s for s in candidates if s != base_assignments[program_id]
        ]:
            # Allow moving onto spaces that are currently unused OR swapping onto unused specialty rooms
            if space_id in occupied and space_id not in free:
                # only if currently unused by any program — skip occupied
                continue
            trial = dict(base_assignments)
            trial[program_id] = space_id
            # ensure uniqueness
            if len(trial.values()) != len(set(trial.values())):
                continue
            score = _score(project, trial)
            if score > base_score + 0.5:
                suggestions.append(
                    {
                        "operator": "move",
                        "description": f"Move {program_id} to {space_id}",
                        "delta_score": round(score - base_score, 2),
                        "assignments": trial,
                        "score": round(score, 2),
                    }
                )

    suggestions.sort(key=lambda s: -s["delta_score"])
    top = suggestions[:max_suggestions]

    # Label as Scheme+1, +2, ...
    labeled = []
    for i, sug in enumerate(top, start=1):
        trial_scheme = Scheme(
            id=f"{scheme.id}+{i}",
            name=f"{scheme.name} / local fix {i}",
            description=sug["description"],
            assignments=sug["assignments"],
        )
        report = evaluate_scheme(project, trial_scheme)
        labeled.append(
            {
                "id": trial_scheme.id,
                "operator": sug["operator"],
                "description": sug["description"],
                "delta_score": sug["delta_score"],
                "metrics": {
                    "score.weighted": report.metrics["score.weighted"],
                    "compliance.score": report.metrics["compliance.score"],
                    "adjacency.score": report.metrics["adjacency.score"],
                    "travel.mean_transition_ft": report.metrics["travel.mean_transition_ft"],
                    "compliance.fail_count": report.metrics["compliance.fail_count"],
                    "passed": report.passed,
                },
                "assignments": sug["assignments"],
            }
        )

    return {
        "base_scheme": scheme.id,
        "base_score": round(base_score, 2),
        "base_fail_count": base_report.metrics["compliance.fail_count"],
        "suggestions": labeled,
    }


def improve_with_cp_sat(
    project: Project,
    scheme: Scheme | str,
    time_limit_s: float = 2.0,
) -> dict:
    """Assign selected movable programs to candidate rooms with OR-Tools CP-SAT.

    Fixed programs stay put; movable programs choose among specialty/commons candidates.
    Falls back to greedy local search result if ortools unavailable.
    """
    if isinstance(scheme, str):
        scheme = project.get_scheme(scheme)

    try:
        from ortools.sat.python import cp_model
    except ImportError:
        result = suggest_local_improvements(project, scheme, max_suggestions=1)
        return {"method": "greedy_fallback", **result}

    movable = ["art", "learning_commons", "music"]
    # Candidate pools by program category heuristic
    pools = {
        "art": [s.id for s in project.floor_plan.spaces if s.id.startswith("s_art")],
        "learning_commons": [
            s.id for s in project.floor_plan.spaces if s.id.startswith("s_commons")
        ],
        "music": [s.id for s in project.floor_plan.spaces if s.id in {"s_music", "s_art_near", "s_art_far"}],
    }

    fixed = {k: v for k, v in scheme.assignments.items() if k not in movable}
    model = cp_model.CpModel()
    vars_: dict[str, dict[str, cp_model.IntVar]] = {}
    for prog in movable:
        if prog not in scheme.assignments:
            continue
        pool = pools.get(prog, [])
        if not pool:
            continue
        vars_[prog] = {space: model.NewBoolVar(f"{prog}_{space}") for space in pool}
        model.Add(sum(vars_[prog].values()) == 1)

    # Unique spaces among movable
    all_spaces = set()
    for prog, mapping in vars_.items():
        all_spaces.update(mapping.keys())
    for space in all_spaces:
        present = [vars_[prog][space] for prog in vars_ if space in vars_[prog]]
        if len(present) > 1:
            model.Add(sum(present) <= 1)
        # Also cannot take a fixed-occupied space
        if space in fixed.values():
            for prog in vars_:
                if space in vars_[prog]:
                    model.Add(vars_[prog][space] == 0)

    # Enumerate feasible assignments and pick best scored (small pools)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.enumerate_all_solutions = True

    class Collector(cp_model.CpSolverSolutionCallback):
        def __init__(self):
            super().__init__()
            self.solutions: list[dict[str, str]] = []

        def on_solution_callback(self):
            assign = dict(fixed)
            for prog, mapping in vars_.items():
                for space, var in mapping.items():
                    if self.Value(var):
                        assign[prog] = space
            self.solutions.append(assign)

    cb = Collector()
    model.Minimize(0)
    solver.Solve(model, cb)

    base_score = _score(project, scheme.assignments)
    best = None
    best_score = base_score
    for assign in cb.solutions:
        # complete with any missing from original
        full = dict(scheme.assignments)
        full.update(assign)
        if len(full.values()) != len(set(full.values())):
            continue
        sc = _score(project, full)
        if sc > best_score:
            best_score = sc
            best = full

    if not best:
        greedy = suggest_local_improvements(project, scheme, max_suggestions=3)
        return {"method": "cp_sat_no_improve", **greedy}

    trial = Scheme(
        id=f"{scheme.id}+cp",
        name=f"{scheme.name} / CP-SAT",
        description="CP-SAT reassignment of movable specialty programs",
        assignments=best,
    )
    report = evaluate_scheme(project, trial)
    return {
        "method": "cp_sat",
        "base_scheme": scheme.id,
        "base_score": round(base_score, 2),
        "suggestions": [
            {
                "id": trial.id,
                "operator": "cp_sat_reassign",
                "description": "Reassign art / learning commons / music via CP-SAT",
                "delta_score": round(best_score - base_score, 2),
                "metrics": {
                    "score.weighted": report.metrics["score.weighted"],
                    "compliance.score": report.metrics["compliance.score"],
                    "adjacency.score": report.metrics["adjacency.score"],
                    "travel.mean_transition_ft": report.metrics["travel.mean_transition_ft"],
                    "compliance.fail_count": report.metrics["compliance.fail_count"],
                    "passed": report.passed,
                },
                "assignments": best,
            }
        ],
    }
