"""Input B — spatial field: floor plan + per-space attributes.

Owns geometry, capacity, dimensions, circulation graph. Does not own programs or ranking.
"""

from school_program_intelligence.b_spatial.graph import (
    all_program_distances,
    build_circulation_graph,
    program_pair_distance,
    route_distance,
    route_path,
    space_to_node,
)
from school_program_intelligence.b_spatial.inspect import show_spatial_field
from school_program_intelligence.b_spatial.space_syntax import spatial_fingerprints, spatial_fit
from school_program_intelligence.shared.load import load_spatial_field
from school_program_intelligence.shared.models import SpatialField

__all__ = [
    "SpatialField",
    "load_spatial_field",
    "show_spatial_field",
    "build_circulation_graph",
    "space_to_node",
    "route_distance",
    "route_path",
    "all_program_distances",
    "program_pair_distance",
    "spatial_fingerprints",
    "spatial_fit",
]
