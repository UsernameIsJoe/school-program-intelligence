from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from school_program_intelligence.evaluation import compare_schemes, diagnose, evaluate_scheme
from school_program_intelligence.optimization import suggest_local_improvements
from school_program_intelligence.program import load_project

APP_DIR = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(APP_DIR / "templates"))

app = FastAPI(title="School Program Intelligence", version="0.1.0")
static_dir = APP_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


def _space_draw(spaces) -> list[dict]:
    drawn = []
    for space in spaces:
        if not space.polygon:
            continue
        xs = [p.x for p in space.polygon]
        ys = [p.y for p in space.polygon]
        drawn.append(
            {
                "id": space.id,
                "label": space.id.replace("s_", ""),
                "is_circulation": space.is_circulation,
                "points": " ".join(f"{p.x},{110 - p.y}" for p in space.polygon),
                "cx": sum(xs) / len(xs),
                "cy": 110 - (sum(ys) / len(ys)),
            }
        )
    return drawn


@app.get("/", response_class=HTMLResponse)
def home(request: Request, fixture: str = "toy_elementary") -> HTMLResponse:
    project = load_project(fixture)
    comparison = compare_schemes(project, fixture_name=fixture)
    return TEMPLATES.TemplateResponse(
        "index.html",
        {
            "request": request,
            "fixture": fixture,
            "project_name": project.name,
            "schemes": project.schemes,
            "comparison": comparison,
            "drawn_spaces": _space_draw(project.floor_plan.spaces),
        },
    )


@app.get("/api/evaluate")
def api_evaluate(fixture: str = "toy_elementary", scheme: str = "A") -> JSONResponse:
    project = load_project(fixture)
    try:
        report = evaluate_scheme(project, scheme, fixture_name=fixture)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    data = report.model_dump()
    data["metrics"].pop("spatial.fingerprints", None)
    data["metrics"].pop("utilization.by_space", None)
    return JSONResponse(data)


@app.get("/api/compare")
def api_compare(fixture: str = "toy_elementary") -> JSONResponse:
    project = load_project(fixture)
    return JSONResponse(compare_schemes(project, fixture_name=fixture))


@app.get("/api/diagnose")
def api_diagnose(fixture: str = "toy_elementary", scheme: str = "B") -> JSONResponse:
    project = load_project(fixture)
    return JSONResponse(diagnose(project, scheme, fixture_name=fixture))


@app.get("/api/improve")
def api_improve(fixture: str = "toy_elementary", scheme: str = "B") -> JSONResponse:
    project = load_project(fixture)
    return JSONResponse(suggest_local_improvements(project, scheme))


@app.get("/scheme/{scheme_id}", response_class=HTMLResponse)
def scheme_view(
    request: Request,
    scheme_id: str,
    fixture: str = Query("toy_elementary"),
) -> HTMLResponse:
    project = load_project(fixture)
    try:
        scheme = project.get_scheme(scheme_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    report = evaluate_scheme(project, scheme, fixture_name=fixture)
    issues = diagnose(project, scheme, fixture_name=fixture)
    improvements = suggest_local_improvements(project, scheme, max_suggestions=3)
    spaces = project.space_map()
    placed = []
    for pid, sid in scheme.assignments.items():
        space = spaces[sid]
        if not space.polygon:
            continue
        xs = [p.x for p in space.polygon]
        ys = [p.y for p in space.polygon]
        placed.append(
            {
                "program_id": pid,
                "space_id": sid,
                "name": space.name,
                "points": " ".join(f"{p.x},{110 - p.y}" for p in space.polygon),
                "cx": sum(xs) / len(xs),
                "cy": 110 - (sum(ys) / len(ys)),
                "area": space.area,
            }
        )
    return TEMPLATES.TemplateResponse(
        "scheme.html",
        {
            "request": request,
            "fixture": fixture,
            "scheme": scheme,
            "report": report,
            "issues": issues,
            "improvements": improvements,
            "placed": placed,
            "summary": report.summarize(),
        },
    )
