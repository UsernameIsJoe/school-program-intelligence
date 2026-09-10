"""Shared models used across A, B, C, engine, and rating.

Owns cross-cutting types only. Component packages own their loaders and behavior.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Importance(str, Enum):
    MUST_TOUCH = "must_touch"
    MUST_NEARBY = "must_nearby"
    SHOULD_NEARBY = "should_nearby"
    WEAK = "weak"
    NEUTRAL = "neutral"
    SHOULD_SEPARATE = "should_separate"


class RelationshipType(str, Enum):
    ADJACENT = "adjacent"
    NEARBY = "nearby"
    VISIBLE = "visible"
    SEPARATED = "separated"


class Point(BaseModel):
    x: float
    y: float


class Door(BaseModel):
    id: str
    to_space: str
    position: Point | None = None


class SpatialPreferences(BaseModel):
    integration: str = "medium"
    visibility: str = "medium"
    privacy: str = "medium"
    accessibility: str = "medium"


class Space(BaseModel):
    id: str
    name: str
    space_type: str = "room"
    floor: int = 1
    area: float
    capacity: int = 0
    polygon: list[Point] = Field(default_factory=list)
    doors: list[Door] = Field(default_factory=list)
    program_type: str | None = None
    is_circulation: bool = False


class Program(BaseModel):
    id: str
    name: str
    category: str
    area_target: float
    area_min: float
    area_max: float
    capacity: int = 0
    spatial_preferences: SpatialPreferences = Field(default_factory=SpatialPreferences)
    required: bool = True
    shared_use: bool = False


class Activity(BaseModel):
    id: str
    name: str
    cohort: str
    size: int
    duration_minutes: int = 50
    space_requirements: list[str] = Field(default_factory=list)


class ScheduleEvent(BaseModel):
    id: str
    time_start: str
    time_end: str
    activity: str
    cohort: str
    students: int
    assigned_program: str
    previous_program: str | None = None


class Relationship(BaseModel):
    source_program: str
    target_program: str
    importance: Importance
    preferred_distance_ft: float | None = None
    relationship_type: RelationshipType = RelationshipType.NEARBY
    hard: bool = False


class PriorityWeights(BaseModel):
    student_travel: float = 1.0
    neighborhood_cohesion: float = 1.0
    shared_space_performance: float = 0.8
    area_efficiency: float = 0.6
    capacity_fit: float = 1.0
    adjacency_fit: float = 1.0
    circulation_stress: float = 0.9


class CorridorEdge(BaseModel):
    id: str
    from_node: str
    to_node: str
    length_ft: float
    width_ft: float = 8.0
    capacity: int = 200
    floor_change: bool = False


class CirculationNode(BaseModel):
    id: str
    kind: str = "junction"
    space_id: str | None = None
    floor: int = 1
    position: Point | None = None


class FloorPlan(BaseModel):
    id: str
    name: str
    spaces: list[Space]
    nodes: list[CirculationNode] = Field(default_factory=list)
    edges: list[CorridorEdge] = Field(default_factory=list)
    entrances: list[str] = Field(default_factory=list)


class Assignment(BaseModel):
    """Program → space map. Used by engine/rating tests — not a product 'scheme search'."""

    id: str
    name: str
    description: str = ""
    mapping: dict[str, str]  # program_id -> space_id


class ProgramWorld(BaseModel):
    """Input A."""

    id: str
    name: str = ""
    programs: list[Program]
    activities: list[Activity] = Field(default_factory=list)
    schedule: list[ScheduleEvent] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)

    def program_map(self) -> dict[str, Program]:
        return {p.id: p for p in self.programs}


class SpatialField(BaseModel):
    """Input B."""

    id: str
    name: str = ""
    floor_plan: FloorPlan

    def space_map(self) -> dict[str, Space]:
        return {s.id: s for s in self.floor_plan.spaces}


class Preferences(BaseModel):
    """Input C defaults for a fixture."""

    id: str = "default"
    prompt: str = ""
    weights: PriorityWeights = Field(default_factory=PriorityWeights)


class Study(BaseModel):
    """Assembled A + B (+ optional C) for engine/rating component tests."""

    id: str
    name: str
    program: ProgramWorld
    spatial: SpatialField
    preferences: Preferences = Field(default_factory=Preferences)
    assignments: list[Assignment] = Field(default_factory=list)

    def program_map(self) -> dict[str, Program]:
        return self.program.program_map()

    def space_map(self) -> dict[str, Space]:
        return self.spatial.space_map()

    def get_assignment(self, assignment_id: str) -> Assignment:
        by_id = {a.id: a for a in self.assignments}
        if assignment_id not in by_id:
            raise KeyError(f"Unknown assignment '{assignment_id}'. Available: {sorted(by_id)}")
        return by_id[assignment_id]

    # Compatibility aliases used inside engine modules
    @property
    def programs(self) -> list[Program]:
        return self.program.programs

    @property
    def schedule(self) -> list[ScheduleEvent]:
        return self.program.schedule

    @property
    def relationships(self) -> list[Relationship]:
        return self.program.relationships

    @property
    def floor_plan(self) -> FloorPlan:
        return self.spatial.floor_plan

    @property
    def priorities(self) -> PriorityWeights:
        return self.preferences.weights


class CheckResult(BaseModel):
    metric_id: str
    status: str
    message: str
    value: Any = None
    expected: Any = None
    program_id: str | None = None
    space_id: str | None = None


class SimulationReport(BaseModel):
    """Engine output: measured metrics only (no C-weighted score)."""

    fixture: str
    assignment_id: str
    assignment_name: str
    checks: list[CheckResult] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    passed: bool = True

    def summarize(self) -> dict[str, int]:
        counts = {"pass": 0, "warn": 0, "fail": 0}
        for c in self.checks:
            counts[c.status] = counts.get(c.status, 0) + 1
        return counts
