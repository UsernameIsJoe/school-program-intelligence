from __future__ import annotations

import argparse
import json

from school_program_intelligence.a_program import load_program_world, show_program_world
from school_program_intelligence.b_spatial import load_spatial_field, show_spatial_field
from school_program_intelligence.c_preferences import interpret_priorities, load_preferences
from school_program_intelligence.engine import diagnose, simulate
from school_program_intelligence.rating import score_report
from school_program_intelligence.shared import load_study


def _print(data: object) -> None:
    print(json.dumps(data, indent=2, default=str))


def cmd_a(args: argparse.Namespace) -> int:
    world = load_program_world(args.fixture)
    _print(show_program_world(world))
    return 0


def cmd_b(args: argparse.Namespace) -> int:
    field = load_spatial_field(args.fixture)
    _print(show_spatial_field(field))
    return 0


def cmd_c(args: argparse.Namespace) -> int:
    prefs = load_preferences(args.fixture)
    prompt = args.prompt if args.prompt is not None else prefs.prompt
    result = interpret_priorities(prompt, base=prefs.weights)
    _print(
        {
            "component": "C",
            "prompt": result.prompt,
            "levels": result.levels,
            "weights": result.weights.model_dump(),
            "notes": result.notes,
        }
    )
    return 0


def cmd_engine(args: argparse.Namespace) -> int:
    study = load_study(args.fixture)
    report = simulate(study, args.assignment, fixture_name=args.fixture)
    payload = report.model_dump()
    if not args.verbose:
        payload["metrics"].pop("spatial.fingerprints", None)
        payload["metrics"].pop("utilization.by_space", None)
        payload["metrics"].pop("circulation.edge_loads", None)
    if args.diagnose:
        payload["diagnosis"] = diagnose(study, args.assignment, fixture_name=args.fixture)
    _print(payload)
    return 0 if report.passed else 1


def cmd_rating(args: argparse.Namespace) -> int:
    study = load_study(args.fixture)
    prefs = study.preferences
    prompt = args.prompt if args.prompt is not None else prefs.prompt
    interpreted = interpret_priorities(prompt, base=prefs.weights)
    report = simulate(study, args.assignment, fixture_name=args.fixture)
    scored = score_report(report, interpreted.weights)
    _print(
        {
            "component": "rating",
            "assignment_id": args.assignment,
            "prompt": interpreted.prompt,
            "score": scored,
            "engine_passed": report.passed,
            "compliance_score": report.metrics.get("compliance.score"),
            "adjacency_score": report.metrics.get("adjacency.score"),
            "mean_transition_ft": report.metrics.get("travel.mean_transition_ft"),
        }
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="spi",
        description="School Program Intelligence — inspect A, B, C, engine, rating components.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_a = sub.add_parser("a", help="Show input A (program world)")
    p_a.add_argument("--fixture", default="toy_elementary")
    p_a.set_defaults(func=cmd_a)

    p_b = sub.add_parser("b", help="Show input B (spatial field)")
    p_b.add_argument("--fixture", default="toy_elementary")
    p_b.set_defaults(func=cmd_b)

    p_c = sub.add_parser("c", help="Interpret preference prompt (input C)")
    p_c.add_argument("--fixture", default="toy_elementary")
    p_c.add_argument("--prompt", default=None, help="Override fixture prompt")
    p_c.set_defaults(func=cmd_c)

    p_e = sub.add_parser("engine", help="Simulate one assignment against A+B")
    p_e.add_argument("--fixture", default="toy_elementary")
    p_e.add_argument("--assignment", default="A")
    p_e.add_argument("--diagnose", action="store_true")
    p_e.add_argument("--verbose", action="store_true")
    p_e.set_defaults(func=cmd_engine)

    p_r = sub.add_parser("rating", help="Score an assignment with C weights")
    p_r.add_argument("--fixture", default="toy_elementary")
    p_r.add_argument("--assignment", default="A")
    p_r.add_argument("--prompt", default=None)
    p_r.set_defaults(func=cmd_rating)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
