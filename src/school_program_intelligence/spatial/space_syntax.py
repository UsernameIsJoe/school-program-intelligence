from __future__ import annotations

import networkx as nx

from school_program_intelligence.program.schema import Project
from school_program_intelligence.spatial.graph import build_circulation_graph, space_to_node


def _preference_score(label: str) -> float:
    return {
        "very_low": 0.0,
        "low": 0.25,
        "medium": 0.5,
        "high": 0.75,
        "very_high": 1.0,
    }.get(label.lower(), 0.5)


def spatial_fingerprints(project: Project) -> dict[str, dict[str, float]]:
    """Lite Space Syntax-style metrics per space."""
    graph = build_circulation_graph(project.floor_plan)
    s2n = space_to_node(project.floor_plan)
    entrances = project.floor_plan.entrances
    fingerprints: dict[str, dict[str, float]] = {}

    undirected = graph
    for space in project.floor_plan.spaces:
        node = s2n.get(space.id)
        if not node or node not in undirected:
            continue
        degree = undirected.degree(node)
        # Integration proxy: inverse of mean shortest-path distance to others
        lengths = []
        for other in undirected.nodes:
            if other == node:
                continue
            try:
                lengths.append(nx.shortest_path_length(undirected, node, other, weight="weight"))
            except nx.NetworkXNoPath:
                continue
        mean_depth = sum(lengths) / len(lengths) if lengths else 999.0
        integration = 1.0 / mean_depth if mean_depth > 0 else 0.0

        depth_from_entry = 0.0
        if entrances:
            entry_depths = []
            for ent in entrances:
                if ent in undirected:
                    try:
                        entry_depths.append(
                            nx.shortest_path_length(undirected, node, ent, weight="weight")
                        )
                    except nx.NetworkXNoPath:
                        pass
            depth_from_entry = min(entry_depths) if entry_depths else 999.0

        # Visibility stub: rooms sharing a corridor junction count as visually related
        neighbors = list(undirected.neighbors(node))
        visibility = min(1.0, len(neighbors) / 4.0)

        fingerprints[space.id] = {
            "connectivity": float(degree),
            "integration": float(integration),
            "mean_depth": float(mean_depth),
            "depth_from_entry": float(depth_from_entry),
            "visibility": float(visibility),
            "circulation_exposure": 1.0 if space.is_circulation else visibility * 0.5,
        }
    return fingerprints


def spatial_fit(project: Project, assignments: dict[str, str]) -> dict[str, float]:
    fps = spatial_fingerprints(project)
    fits: dict[str, float] = {}
    for program in project.programs:
        space_id = assignments.get(program.id)
        if not space_id or space_id not in fps:
            continue
        fp = fps[space_id]
        pref = program.spatial_preferences
        desired = {
            "integration": _preference_score(pref.integration),
            "visibility": _preference_score(pref.visibility),
            # privacy desired high => want low visibility
            "privacy": _preference_score(pref.privacy),
        }
        # Normalize integration to 0-1 via relative rank-ish clamp
        integ_norm = min(1.0, fp["integration"] * 50.0)
        vis = fp["visibility"]
        privacy_actual = 1.0 - vis
        err = (
            abs(desired["integration"] - integ_norm)
            + abs(desired["visibility"] - vis)
            + abs(desired["privacy"] - privacy_actual)
        )
        fits[program.id] = max(0.0, 100.0 * (1.0 - err / 3.0))
    return fits
