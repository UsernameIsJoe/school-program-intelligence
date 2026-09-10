from __future__ import annotations

import argparse
import json
import sys

from school_program_intelligence.evaluation import compare_schemes, diagnose, evaluate_scheme
from school_program_intelligence.optimization import improve_with_cp_sat, suggest_local_improvements
from school_program_intelligence.program import load_project


def _print(data: object, as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, indent=2, default=str))
        return
    if isinstance(data, dict):
        print(json.dumps(data, indent=2, default=str))
    else:
        print(data)


def cmd_evaluate(args: argparse.Namespace) -> int:
    project = load_project(args.fixture)
    report = evaluate_scheme(project, args.scheme, fixture_name=args.fixture)
    payload = report.model_dump()
    if not args.verbose:
        # Keep CLI readable: drop bulky fingerprints / full utilization unless verbose
        metrics = payload["metrics"]
        metrics.pop("spatial.fingerprints", None)
        metrics.pop("utilization.by_space", None)
        metrics.pop("circulation.edge_loads", None)
        if not args.verbose:
            metrics["adjacency.pairs"] = [
                p for p in metrics.get("adjacency.pairs", []) if p.get("penalty", 0) > 0
            ]
    _print(payload, args.json)
    return 0 if report.passed else 1


def cmd_compare(args: argparse.Namespace) -> int:
    project = load_project(args.fixture)
    result = compare_schemes(project, fixture_name=args.fixture)
    _print(result, args.json)
    return 0


def cmd_diagnose(args: argparse.Namespace) -> int:
    project = load_project(args.fixture)
    result = diagnose(project, args.scheme, fixture_name=args.fixture)
    _print(result, args.json)
    return 0 if result["issue_count"] == 0 else 1


def cmd_improve(args: argparse.Namespace) -> int:
    project = load_project(args.fixture)
    if args.method == "cp_sat":
        result = improve_with_cp_sat(project, args.scheme)
    else:
        result = suggest_local_improvements(project, args.scheme, max_suggestions=args.max)
    _print(result, args.json)
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    try:
        import uvicorn
    except ImportError as exc:
        print("Install web extras: pip install -e \".[web]\"", file=sys.stderr)
        raise SystemExit(1) from exc
    uvicorn.run(
        "school_program_intelligence.web.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="spi",
        description="School Program Intelligence — evaluate and compare school program schemes.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--fixture", default="toy_elementary", help="Fixture name under data/examples/")
        p.add_argument("--json", action="store_true", help="Force JSON output")

    p_eval = sub.add_parser("evaluate", help="Evaluate one scheme")
    add_common(p_eval)
    p_eval.add_argument("--scheme", default="A")
    p_eval.add_argument("--verbose", action="store_true")
    p_eval.set_defaults(func=cmd_evaluate)

    p_cmp = sub.add_parser("compare", help="Compare all schemes in a fixture")
    add_common(p_cmp)
    p_cmp.set_defaults(func=cmd_compare)

    p_diag = sub.add_parser("diagnose", help="List metric-backed issues for a scheme")
    add_common(p_diag)
    p_diag.add_argument("--scheme", default="B")
    p_diag.set_defaults(func=cmd_diagnose)

    p_imp = sub.add_parser("improve", help="Suggest local program moves/swaps")
    add_common(p_imp)
    p_imp.add_argument("--scheme", default="B")
    p_imp.add_argument("--method", choices=["greedy", "cp_sat"], default="greedy")
    p_imp.add_argument("--max", type=int, default=5)
    p_imp.set_defaults(func=cmd_improve)

    p_serve = sub.add_parser("serve", help="Run thin FastAPI web UI")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)
    p_serve.add_argument("--reload", action="store_true")
    p_serve.set_defaults(func=cmd_serve)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
