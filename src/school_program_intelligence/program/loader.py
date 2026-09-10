from __future__ import annotations

from pathlib import Path

import yaml

from school_program_intelligence.program.schema import Project

PACKAGE_ROOT = Path(__file__).resolve().parents[3]
DATA_EXAMPLES = PACKAGE_ROOT / "data" / "examples"


def fixture_path(name: str) -> Path:
    path = DATA_EXAMPLES / name
    if not path.exists():
        raise FileNotFoundError(f"Fixture not found: {path}")
    return path


def load_project(fixture: str | Path) -> Project:
    root = Path(fixture) if isinstance(fixture, Path) else fixture_path(fixture)
    if root.is_file():
        data = yaml.safe_load(root.read_text(encoding="utf-8"))
        return Project.model_validate(data)

    project_file = root / "project.yaml"
    if not project_file.exists():
        raise FileNotFoundError(f"Expected project.yaml in {root}")

    data = yaml.safe_load(project_file.read_text(encoding="utf-8")) or {}

    for key, filename in (
        ("programs", "programs.yaml"),
        ("relationships", "relationships.yaml"),
        ("schedule", "schedule.yaml"),
        ("activities", "activities.yaml"),
        ("floor_plan", "floor_plan.yaml"),
        ("schemes", "schemes.yaml"),
        ("priorities", "priorities.yaml"),
    ):
        part = root / filename
        if part.exists():
            loaded = yaml.safe_load(part.read_text(encoding="utf-8"))
            if key == "priorities" and isinstance(loaded, dict) and key not in loaded:
                data[key] = loaded
            elif isinstance(loaded, dict) and key in loaded:
                data[key] = loaded[key]
            else:
                data[key] = loaded

    return Project.model_validate(data)
