from __future__ import annotations

import networkx as nx

from school_program_intelligence.program.schema import FloorPlan, Project


def build_circulation_graph(floor_plan: FloorPlan) -> nx.Graph:
    g = nx.Graph()
    for node in floor_plan.nodes:
        g.add_node(
            node.id,
            kind=node.kind,
            space_id=node.space_id,
            floor=node.floor,
        )
    for edge in floor_plan.edges:
        g.add_edge(
            edge.from_node,
            edge.to_node,
            id=edge.id,
            length_ft=edge.length_ft,
            width_ft=edge.width_ft,
            capacity=edge.capacity,
            floor_change=edge.floor_change,
            weight=edge.length_ft,
        )
    return g


def space_to_node(floor_plan: FloorPlan) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for node in floor_plan.nodes:
        if node.space_id:
            mapping[node.space_id] = node.id
    return mapping


def route_distance(graph: nx.Graph, source_node: str, target_node: str) -> float | None:
    if source_node not in graph or target_node not in graph:
        return None
    try:
        return float(nx.shortest_path_length(graph, source_node, target_node, weight="weight"))
    except nx.NetworkXNoPath:
        return None


def route_path(graph: nx.Graph, source_node: str, target_node: str) -> list[str]:
    try:
        return list(nx.shortest_path(graph, source_node, target_node, weight="weight"))
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []


def all_program_distances(project: Project, scheme_assignments: dict[str, str]) -> dict[tuple[str, str], float]:
    graph = build_circulation_graph(project.floor_plan)
    s2n = space_to_node(project.floor_plan)
    distances: dict[tuple[str, str], float] = {}
    space_ids = list(scheme_assignments.values())
    for i, a in enumerate(space_ids):
        for b in space_ids[i + 1 :]:
            na, nb = s2n.get(a), s2n.get(b)
            if not na or not nb:
                continue
            d = route_distance(graph, na, nb)
            if d is not None:
                distances[(a, b)] = d
                distances[(b, a)] = d
    return distances


def program_pair_distance(
    project: Project,
    assignments: dict[str, str],
    program_a: str,
    program_b: str,
) -> float | None:
    graph = build_circulation_graph(project.floor_plan)
    s2n = space_to_node(project.floor_plan)
    sa, sb = assignments.get(program_a), assignments.get(program_b)
    if not sa or not sb:
        return None
    na, nb = s2n.get(sa), s2n.get(sb)
    if not na or not nb:
        return None
    return route_distance(graph, na, nb)
