from __future__ import annotations

from pathlib import Path

import yaml

from school_program_intelligence.shared.models import (
    Assignment,
    Preferences,
    PriorityWeights,
    ProgramWorld,
    SpatialField,
    Study,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = PACKAGE_ROOT / "data"


def _load_yaml(path: Path) -> dict | list:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _merge_part(data: dict, key: str, path: Path) -> None:
    if not path.exists():
        return
    loaded = _load_yaml(path)
    if key == "priorities" and isinstance(loaded, dict) and key not in loaded and "weights" not in loaded:
        data[key] = loaded
    elif isinstance(loaded, dict) and key in loaded:
        data[key] = loaded[key]
    elif isinstance(loaded, dict) and "weights" in loaded and key == "preferences":
        data[key] = loaded
    else:
        data[key] = loaded


def load_program_world(fixture: str = "toy_elementary") -> ProgramWorld:
    root = DATA_ROOT / "a_program" / fixture
    if not root.exists():
        raise FileNotFoundError(f"A fixture not found: {root}")
    meta = _load_yaml(root / "meta.yaml") if (root / "meta.yaml").exists() else {"id": fixture, "name": fixture}
    data = {"id": meta.get("id", fixture), "name": meta.get("name", fixture)}
    _merge_part(data, "programs", root / "programs.yaml")
    _merge_part(data, "relationships", root / "relationships.yaml")
    _merge_part(data, "schedule", root / "schedule.yaml")
    _merge_part(data, "activities", root / "activities.yaml")
    return ProgramWorld.model_validate(data)


def load_spatial_field(fixture: str = "toy_elementary") -> SpatialField:
    root = DATA_ROOT / "b_spatial" / fixture
    if not root.exists():
        raise FileNotFoundError(f"B fixture not found: {root}")
    meta = _load_yaml(root / "meta.yaml") if (root / "meta.yaml").exists() else {"id": fixture, "name": fixture}
    data = {"id": meta.get("id", fixture), "name": meta.get("name", fixture)}
    fp = root / "floor_plan.yaml"
    loaded = _load_yaml(fp)
    data["floor_plan"] = loaded["floor_plan"] if isinstance(loaded, dict) and "floor_plan" in loaded else loaded
    return SpatialField.model_validate(data)


def load_preferences(fixture: str = "toy_elementary") -> Preferences:
    root = DATA_ROOT / "c_preferences" / fixture
    if not root.exists():
        raise FileNotFoundError(f"C fixture not found: {root}")
    data: dict = {"id": fixture}
    prompt_file = root / "prompt.txt"
    if prompt_file.exists():
        data["prompt"] = prompt_file.read_text(encoding="utf-8").strip()
    weights_file = root / "weights.yaml"
    if weights_file.exists():
        loaded = _load_yaml(weights_file)
        if isinstance(loaded, dict) and "weights" in loaded:
            data["weights"] = loaded["weights"]
            if loaded.get("prompt") and "prompt" not in data:
                data["prompt"] = loaded["prompt"]
        else:
            data["weights"] = loaded
    return Preferences.model_validate(data)


def load_assignments(fixture: str = "toy_elementary") -> list[Assignment]:
    path = DATA_ROOT / "assignments" / fixture / "assignments.yaml"
    if not path.exists():
        return []
    loaded = _load_yaml(path)
    items = loaded["assignments"] if isinstance(loaded, dict) and "assignments" in loaded else loaded
    # Support legacy "assignments:" key as mapping field name in YAML as "mapping" or nested
    out = []
    for item in items:
        if "mapping" not in item and "assignments" in item:
            item = {**item, "mapping": item.pop("assignments")}
        out.append(Assignment.model_validate(item))
    return out


def load_study(fixture: str = "toy_elementary") -> Study:
    """Assemble A + B + C + test assignments for engine/rating."""
    program = load_program_world(fixture)
    spatial = load_spatial_field(fixture)
    try:
        preferences = load_preferences(fixture)
    except FileNotFoundError:
        preferences = Preferences(id=fixture, weights=PriorityWeights())
    assignments = load_assignments(fixture)
    return Study(
        id=fixture,
        name=program.name or fixture,
        program=program,
        spatial=spatial,
        preferences=preferences,
        assignments=assignments,
    )
