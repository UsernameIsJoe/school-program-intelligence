from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from school_program_intelligence.evaluation import compare_schemes, diagnose, evaluate_scheme
from school_program_intelligence.llm import interpret_priorities
from school_program_intelligence.optimization import suggest_local_improvements
from school_program_intelligence.program import load_project
from school_program_intelligence.program.schema import PriorityWeights
from school_program_intelligence.web.viz import bubble_diagram, plan_overlays

APP_DIR = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(APP_DIR / "templates"))

app = FastAPI(title="School Program Intelligence", version="0.2.0")
static_dir = APP_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


class PriorityPromptIn(BaseModel):
    fixture: str = "toy_elementary"
    prompt: str = ""
    weights: PriorityWeights | None = None


class StudioIn(BaseModel):
    fixture: str = "toy_elementary"
    scheme: str = "B"
    prompt: str = ""
    weights: PriorityWeights | None = None
    suggestion_index: int | None = Field(default=None, ge=0)


def _priorities_for(project, prompt: str, weights: PriorityWeights | None) -> tuple[PriorityWeights, dict]:
    if weights is not None:
        interp = interpret_priorities(prompt, base=weights) if prompt.strip() else None
        return weights, {
            "prompt": prompt,
            "levels": {k: "custom" for k in PriorityWeights.model_fields},
            "notes": ["Using manually supplied weights."]
            + (interp.notes if interp else []),
            "weights": weights.model_dump(),
        }
    interp = interpret_priorities(prompt, base=project.priorities)
    return interp.weights, {
        "prompt": interp.prompt,
        "levels": interp.levels,
        "notes": interp.notes,
        "weights": interp.weights.model_dump(),
    }


@app.get("/", response_class=HTMLResponse)
def home(request: Request, fixture: str = "toy_elementary") -> HTMLResponse:
    project = load_project(fixture)
    return TEMPLATES.TemplateResponse(
        request,
        "studio.html",
        {
            "fixture": fixture,
            "project_name": project.name,
            "schemes": [{"id": s.id, "name": s.name} for s in project.schemes],
            "default_prompt": (
                "We care most about maintaining grade neighborhoods and minimizing student travel. "
                "Shared learning commons matter. We are willing to accept slightly less area efficiency."
            ),
            "default_weights": project.priorities.model_dump(),
            "initial_scheme": "B",
        },
    )


@app.post("/api/priorities")
def api_priorities(body: PriorityPromptIn) -> JSONResponse:
    project = load_project(body.fixture)
    _, meta = _priorities_for(project, body.prompt, body.weights)
    return JSONResponse(meta)


@app.post("/api/studio")
def api_studio(body: StudioIn) -> JSONResponse:
    project = load_project(body.fixture)
    try:
        scheme = project.get_scheme(body.scheme)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    priorities, meta = _priorities_for(project, body.prompt, body.weights)
    comparison = compare_schemes(project, fixture_name=body.fixture, priorities=priorities)
    report = evaluate_scheme(project, scheme, fixture_name=body.fixture, priorities=priorities)
    issues = diagnose(project, scheme, fixture_name=body.fixture)
    improvements = suggest_local_improvements(project, scheme, max_suggestions=5)

    suggestion = None
    if body.suggestion_index is not None and body.suggestion_index < len(improvements["suggestions"]):
        suggestion = improvements["suggestions"][body.suggestion_index]

    pairs = report.metrics.get("adjacency.pairs", [])
    bubbles = bubble_diagram(project, scheme, pair_penalties=pairs)
    overlays = plan_overlays(project, scheme, issues.get("issues", []), suggestion=suggestion)

    slim_report = report.model_dump()
    slim_report["metrics"].pop("spatial.fingerprints", None)
    slim_report["metrics"].pop("utilization.by_space", None)
    slim_report["metrics"].pop("circulation.edge_loads", None)

    return JSONResponse(
        {
            "priorities": meta,
            "comparison": comparison,
            "report": slim_report,
            "issues": issues,
            "improvements": improvements,
            "bubbles": bubbles,
            "plan": overlays,
            "active_suggestion": suggestion,
            "scheme": {"id": scheme.id, "name": scheme.name, "description": scheme.description},
        }
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


# Keep deep-link scheme pages working
@app.get("/scheme/{scheme_id}", response_class=HTMLResponse)
def scheme_redirect(request: Request, scheme_id: str, fixture: str = Query("toy_elementary")) -> HTMLResponse:
    return TEMPLATES.TemplateResponse(
        request,
        "studio.html",
        {
            "fixture": fixture,
            "project_name": load_project(fixture).name,
            "schemes": [{"id": s.id, "name": s.name} for s in load_project(fixture).schemes],
            "default_prompt": "",
            "default_weights": load_project(fixture).priorities.model_dump(),
            "initial_scheme": scheme_id,
        },
    )
