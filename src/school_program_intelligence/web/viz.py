from __future__ import annotations

import math
from collections import defaultdict

from school_program_intelligence.program.schema import PriorityWeights, Project, Scheme

# Neurones-inspired category colors (UI palette bar order remapped to program types)
CATEGORY_COLORS = {
    "classroom": "#00D4FF",
    "shared_learning": "#FF4DA6",
    "specialty": "#7CFF3F",
    "support": "#F5E6A3",
    "admin": "#3D5AFE",
    "dining": "#FF5A1F",
    "other": "#B0B8C8",
}

CATEGORY_ORDER = [
    "classroom",
    "shared_learning",
    "specialty",
    "support",
    "admin",
    "dining",
    "other",
]


def _cat_color(category: str) -> str:
    return CATEGORY_COLORS.get(category, CATEGORY_COLORS["other"])


def bubble_diagram(project: Project, scheme: Scheme, pair_penalties: list[dict] | None = None) -> dict:
    """Organic radial bubble diagram: category clusters + ribbon relationships.

    Style reference: systems / roots diagram — sized bubbles, soft cluster clouds,
    thick translucent curved ribbons. Colors from Neurones palette.
    """
    spaces = project.space_map()
    programs = project.program_map()

    # Group programs by category for radial clusters
    by_cat: dict[str, list[str]] = defaultdict(list)
    for pid in scheme.assignments:
        prog = programs.get(pid)
        if not prog:
            continue
        cat = prog.category if prog.category in CATEGORY_COLORS else "other"
        by_cat[cat].append(pid)

    cats = [c for c in CATEGORY_ORDER if by_cat.get(c)]
    n_cats = max(len(cats), 1)
    cx0, cy0 = 200.0, 200.0
    ring_r = 118.0
    nodes: list[dict] = []
    clusters: list[dict] = []

    for i, cat in enumerate(cats):
        angle = -math.pi / 2 + (2 * math.pi * i / n_cats)
        cluster_cx = cx0 + ring_r * math.cos(angle)
        cluster_cy = cy0 + ring_r * math.sin(angle)
        members = by_cat[cat]
        # Cluster cloud radius grows with membership / area
        areas = [programs[p].area_target for p in members if p in programs]
        cloud_r = 28 + min(42, 4 * len(members) + (sum(areas) ** 0.5) / 18)
        label_x = cx0 + (ring_r + 78) * math.cos(angle)
        label_y = cy0 + (ring_r + 78) * math.sin(angle)
        clusters.append(
            {
                "id": cat,
                "label": cat.replace("_", " ").upper(),
                "cx": cluster_cx,
                "cy": cluster_cy,
                "r": cloud_r,
                "color": _cat_color(cat),
                "label_x": label_x,
                "label_y": label_y,
            }
        )
        for j, pid in enumerate(members):
            prog = programs[pid]
            space = spaces.get(scheme.assignments[pid])
            # Fan members inside the cloud
            if len(members) == 1:
                ox = oy = 0.0
            else:
                a2 = angle + (j - (len(members) - 1) / 2) * 0.35
                dist = 10 + (j % 3) * 9
                ox = dist * math.cos(a2 + 0.4)
                oy = dist * math.sin(a2 + 0.4)
            r = max(14.0, min(36.0, (prog.area_target ** 0.5) / 2.8))
            nodes.append(
                {
                    "id": pid,
                    "label": prog.name,
                    "short": prog.name.replace("Classroom", "CR").replace("Learning Commons", "Commons"),
                    "category": cat,
                    "space_id": scheme.assignments[pid],
                    "cx": cluster_cx + ox,
                    "cy": cluster_cy + oy,
                    "r": r,
                    "area": space.area if space else prog.area_target,
                    "color": _cat_color(cat),
                }
            )

    by_id = {n["id"]: n for n in nodes}
    pen_lookup = {}
    for p in pair_penalties or []:
        pen_lookup[(p["source"], p["target"])] = p
        pen_lookup[(p["target"], p["source"])] = p

    ribbons = []
    for rel in project.relationships:
        a, b = by_id.get(rel.source_program), by_id.get(rel.target_program)
        if not a or not b:
            continue
        pen = pen_lookup.get((rel.source_program, rel.target_program), {})
        penalty = float(pen.get("penalty") or 0)
        # Quadratic control point pulled toward diagram center for organic ribbon
        mx = (a["cx"] + b["cx"]) / 2
        my = (a["cy"] + b["cy"]) / 2
        cpx = mx * 0.45 + cx0 * 0.55
        cpy = my * 0.45 + cy0 * 0.55
        width = 6 + (2.5 if rel.hard else 0) + min(10, penalty * 12)
        # Stress tints ribbon warmer; healthy links stay cooler cyan/pink mix
        if penalty >= 0.4:
            color = "#FF5A1F"
            opacity = 0.55
        elif penalty > 0:
            color = "#F5E6A3"
            opacity = 0.4
        else:
            color = a["color"]
            opacity = 0.28
        ribbons.append(
            {
                "source": rel.source_program,
                "target": rel.target_program,
                "importance": rel.importance.value,
                "hard": rel.hard,
                "penalty": penalty,
                "distance_ft": pen.get("distance_ft"),
                "x1": a["cx"],
                "y1": a["cy"],
                "x2": b["cx"],
                "y2": b["cy"],
                "cpx": cpx,
                "cpy": cpy,
                "width": width,
                "color": color,
                "opacity": opacity,
                "path": f"M {a['cx']:.2f},{a['cy']:.2f} Q {cpx:.2f},{cpy:.2f} {b['cx']:.2f},{b['cy']:.2f}",
            }
        )

    return {
        "width": 400,
        "height": 400,
        "center": {"x": cx0, "y": cy0},
        "clusters": clusters,
        "nodes": nodes,
        "edges": ribbons,
        "palette": CATEGORY_COLORS,
    }


def plan_overlays(
    project: Project,
    scheme: Scheme,
    issues: list[dict],
    suggestion: dict | None = None,
) -> list[dict]:
    """Color each assigned space by issue severity; mark suggestion from/to."""
    spaces = project.space_map()
    severity_rank = {"high": 3, "medium": 2, "low": 1}
    space_severity: dict[str, str] = {}
    space_messages: dict[str, list[str]] = {}

    for issue in issues:
        sid = issue.get("space_id")
        pid = issue.get("program_id")
        if not sid and pid:
            sid = scheme.assignments.get(pid)
        evidence = issue.get("evidence") or {}
        targets = []
        if sid:
            targets.append(sid)
        for key in ("source", "target"):
            if key in evidence and evidence[key] in scheme.assignments:
                targets.append(scheme.assignments[evidence[key]])
        if issue.get("metric_id") == "adjacency.distance":
            msg = issue.get("message", "")
            for prog_id in scheme.assignments:
                if prog_id in msg:
                    targets.append(scheme.assignments[prog_id])
        for t in targets:
            sev = issue.get("severity", "low")
            prev = space_severity.get(t)
            if prev is None or severity_rank.get(sev, 0) > severity_rank.get(prev, 0):
                space_severity[t] = sev
            space_messages.setdefault(t, []).append(issue.get("message", ""))

    from_spaces: set[str] = set()
    to_spaces: set[str] = set()
    if suggestion and suggestion.get("assignments"):
        new_assign = suggestion["assignments"]
        for pid, old_sid in scheme.assignments.items():
            new_sid = new_assign.get(pid)
            if new_sid and new_sid != old_sid:
                from_spaces.add(old_sid)
                to_spaces.add(new_sid)

    drawn = []
    for pid, sid in scheme.assignments.items():
        space = spaces.get(sid)
        if not space or not space.polygon:
            continue
        xs = [p.x for p in space.polygon]
        ys = [p.y for p in space.polygon]
        prog = project.program_map().get(pid)
        cat = prog.category if prog else "other"
        role = "ok"
        if sid in from_spaces:
            role = "suggest_from"
        elif sid in to_spaces:
            role = "suggest_to"
        elif space_severity.get(sid) == "high":
            role = "issue_high"
        elif space_severity.get(sid) == "medium":
            role = "issue_medium"
        elif space_severity.get(sid) == "low":
            role = "issue_low"
        drawn.append(
            {
                "program_id": pid,
                "space_id": sid,
                "label": pid,
                "points": " ".join(f"{p.x},{110 - p.y}" for p in space.polygon),
                "cx": sum(xs) / len(xs),
                "cy": 110 - (sum(ys) / len(ys)),
                "role": role,
                "color": _cat_color(cat),
                "messages": space_messages.get(sid, [])[:3],
            }
        )

    assigned = set(scheme.assignments.values())
    for space in project.floor_plan.spaces:
        if space.id in assigned or not space.polygon:
            continue
        xs = [p.x for p in space.polygon]
        ys = [p.y for p in space.polygon]
        if space.id in to_spaces:
            role = "suggest_to"
        elif space.id in from_spaces:
            role = "suggest_from"
        elif space.is_circulation:
            role = "circ"
        else:
            role = "empty"
        drawn.append(
            {
                "program_id": None,
                "space_id": space.id,
                "label": space.id.replace("s_", ""),
                "points": " ".join(f"{p.x},{110 - p.y}" for p in space.polygon),
                "cx": sum(xs) / len(xs),
                "cy": 110 - (sum(ys) / len(ys)),
                "role": role,
                "color": "#2a2a2a",
                "messages": space_messages.get(space.id, [])[:3],
            }
        )
    return drawn


def apply_priority_weights(project: Project, weights: PriorityWeights) -> Project:
    data = project.model_dump()
    data["priorities"] = weights.model_dump()
    return Project.model_validate(data)
