from __future__ import annotations

from school_program_intelligence.shared.models import Space, SpatialField


def _dims(space: Space) -> dict:
    if not space.polygon or len(space.polygon) < 2:
        return {"width_ft": None, "depth_ft": None}
    xs = [p.x for p in space.polygon]
    ys = [p.y for p in space.polygon]
    return {"width_ft": round(max(xs) - min(xs), 1), "depth_ft": round(max(ys) - min(ys), 1)}


def show_spatial_field(field: SpatialField) -> dict:
    spaces = []
    for s in field.floor_plan.spaces:
        d = _dims(s)
        spaces.append(
            {
                "id": s.id,
                "name": s.name,
                "space_type": s.space_type,
                "floor": s.floor,
                "area_sf": s.area,
                "capacity": s.capacity,
                "is_circulation": s.is_circulation,
                "width_ft": d["width_ft"],
                "depth_ft": d["depth_ft"],
            }
        )
    return {
        "component": "B",
        "id": field.id,
        "name": field.name,
        "floor_plan": {
            "id": field.floor_plan.id,
            "name": field.floor_plan.name,
            "entrances": field.floor_plan.entrances,
            "nodes": len(field.floor_plan.nodes),
            "edges": len(field.floor_plan.edges),
        },
        "counts": {
            "spaces": len(spaces),
            "assignable": sum(1 for s in spaces if not s["is_circulation"]),
            "circulation": sum(1 for s in spaces if s["is_circulation"]),
        },
        "spaces": spaces,
    }
