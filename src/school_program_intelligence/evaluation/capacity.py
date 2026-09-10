from __future__ import annotations

from school_program_intelligence.program.schema import (
    CheckResult,
    EvaluationReport,
    Importance,
    Project,
    Scheme,
)


def _space_for_program(scheme: Scheme, program_id: str) -> str | None:
    return scheme.assignments.get(program_id)


def check_program_presence(project: Project, scheme: Scheme) -> list[CheckResult]:
    results: list[CheckResult] = []
    assigned_spaces = set(scheme.assignments.values())
    for program in project.programs:
        if not program.required:
            continue
        space_id = _space_for_program(scheme, program.id)
        if not space_id:
            results.append(
                CheckResult(
                    metric_id="compliance.presence",
                    status="fail",
                    message=f"Required program '{program.name}' is not assigned.",
                    program_id=program.id,
                )
            )
        elif space_id not in project.space_map():
            results.append(
                CheckResult(
                    metric_id="compliance.presence",
                    status="fail",
                    message=f"Program '{program.name}' assigned to unknown space '{space_id}'.",
                    program_id=program.id,
                    space_id=space_id,
                )
            )
        else:
            results.append(
                CheckResult(
                    metric_id="compliance.presence",
                    status="pass",
                    message=f"Program '{program.name}' present in {space_id}.",
                    program_id=program.id,
                    space_id=space_id,
                )
            )
    # Detect double-booking of non-circulation spaces
    reverse: dict[str, list[str]] = {}
    for pid, sid in scheme.assignments.items():
        reverse.setdefault(sid, []).append(pid)
    for sid, pids in reverse.items():
        if len(pids) > 1:
            results.append(
                CheckResult(
                    metric_id="compliance.unique_assignment",
                    status="fail",
                    message=f"Space '{sid}' assigned to multiple programs: {pids}.",
                    space_id=sid,
                    value=pids,
                )
            )
    return results


def check_area_fit(project: Project, scheme: Scheme) -> list[CheckResult]:
    results: list[CheckResult] = []
    spaces = project.space_map()
    for program in project.programs:
        space_id = _space_for_program(scheme, program.id)
        if not space_id or space_id not in spaces:
            continue
        space = spaces[space_id]
        if space.area < program.area_min:
            status = "fail"
            msg = (
                f"{program.name}: area {space.area:.0f} sf below minimum "
                f"{program.area_min:.0f} sf (target {program.area_target:.0f})."
            )
        elif space.area > program.area_max:
            status = "warn"
            msg = (
                f"{program.name}: area {space.area:.0f} sf above preferred max "
                f"{program.area_max:.0f} sf."
            )
        else:
            status = "pass"
            msg = f"{program.name}: area {space.area:.0f} sf within range."
        results.append(
            CheckResult(
                metric_id="compliance.area",
                status=status,
                message=msg,
                value=space.area,
                expected={"min": program.area_min, "max": program.area_max, "target": program.area_target},
                program_id=program.id,
                space_id=space_id,
            )
        )
    return results


def check_capacity_fit(project: Project, scheme: Scheme) -> list[CheckResult]:
    results: list[CheckResult] = []
    spaces = project.space_map()
    # Peak demand per program from schedule
    demand: dict[str, int] = {}
    for event in project.schedule:
        demand[event.assigned_program] = max(demand.get(event.assigned_program, 0), event.students)

    for program in project.programs:
        space_id = _space_for_program(scheme, program.id)
        if not space_id or space_id not in spaces:
            continue
        space = spaces[space_id]
        peak = demand.get(program.id, 0)
        capacity = space.capacity or program.capacity
        if peak and capacity and peak > capacity:
            status = "fail"
            msg = f"{program.name}: peak demand {peak} exceeds capacity {capacity}."
        elif peak and capacity:
            status = "pass"
            msg = f"{program.name}: peak demand {peak} within capacity {capacity}."
        else:
            status = "pass"
            msg = f"{program.name}: no scheduled peak demand to check."
        results.append(
            CheckResult(
                metric_id="compliance.capacity",
                status=status,
                message=msg,
                value={"peak": peak, "capacity": capacity},
                program_id=program.id,
                space_id=space_id,
            )
        )
    return results


def check_hard_relationships(project: Project, scheme: Scheme, distances: dict[tuple[str, str], float] | None = None) -> list[CheckResult]:
    """Hard relationships: must_touch / must_nearby within preferred distance when distances known;
    without distances, only check both programs assigned.
    """
    results: list[CheckResult] = []
    for rel in project.relationships:
        if not rel.hard:
            continue
        s_a = _space_for_program(scheme, rel.source_program)
        s_b = _space_for_program(scheme, rel.target_program)
        if not s_a or not s_b:
            results.append(
                CheckResult(
                    metric_id="compliance.hard_relationship",
                    status="fail",
                    message=(
                        f"Hard relationship {rel.source_program}↔{rel.target_program} "
                        f"missing assignment."
                    ),
                    value=rel.importance.value,
                )
            )
            continue

        if distances is None:
            results.append(
                CheckResult(
                    metric_id="compliance.hard_relationship",
                    status="pass",
                    message=(
                        f"Hard relationship {rel.source_program}↔{rel.target_program}: "
                        f"both assigned ({s_a}, {s_b}); distance deferred."
                    ),
                    space_id=s_a,
                )
            )
            continue

        dist = distances.get((s_a, s_b), distances.get((s_b, s_a)))
        threshold = rel.preferred_distance_ft
        if dist is None:
            status = "fail"
            msg = f"No route between {s_a} and {s_b} for hard relationship."
        elif threshold is not None and dist > threshold:
            status = "fail"
            msg = (
                f"{rel.source_program}↔{rel.target_program}: distance {dist:.0f} ft "
                f"exceeds hard threshold {threshold:.0f} ft ({rel.importance.value})."
            )
        else:
            status = "pass"
            msg = (
                f"{rel.source_program}↔{rel.target_program}: distance "
                f"{dist:.0f} ft within hard threshold."
            )
        results.append(
            CheckResult(
                metric_id="compliance.hard_relationship",
                status=status,
                message=msg,
                value=dist,
                expected=threshold,
                program_id=rel.source_program,
                space_id=s_a,
            )
        )
    return results


def evaluate_compliance(project: Project, scheme: Scheme, distances: dict[tuple[str, str], float] | None = None) -> EvaluationReport:
    checks: list[CheckResult] = []
    checks.extend(check_program_presence(project, scheme))
    checks.extend(check_area_fit(project, scheme))
    checks.extend(check_capacity_fit(project, scheme))
    checks.extend(check_hard_relationships(project, scheme, distances=distances))

    fails = sum(1 for c in checks if c.status == "fail")
    return EvaluationReport(
        fixture=project.id,
        scheme_id=scheme.id,
        scheme_name=scheme.name,
        checks=checks,
        metrics={
            "compliance.fail_count": fails,
            "compliance.warn_count": sum(1 for c in checks if c.status == "warn"),
            "compliance.pass_count": sum(1 for c in checks if c.status == "pass"),
            "compliance.score": max(0.0, 100.0 - 8.0 * fails),
        },
        passed=fails == 0,
    )
