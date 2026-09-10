# Setup & Development Plan

This document records the agreed setup and phased build order for **School Program Intelligence**.

## Product in one line

Make the educational program **executable**: evaluate partially fixed school schemes as `SPACE × ACTIVITY × PEOPLE × TIME × RULES`, then compare, diagnose, and suggest small improvements — with metrics measured by code and explanations handled by an LLM.

## Primary user & moment

- **Who:** architects (internal programming / DD), communicating with school stakeholders  
- **When:** building ~60–80% fixed; programs, adjacencies, and local geometry still movable  
- **Not:** generate a school from nothing

## Core principle

> LLM interprets and explains. Deterministic engines measure.

## Repo layout (scaffolded)

Matches README §24:

| Path | Role |
|------|------|
| `docs/` | research, MSBA notes, precedents, methodology |
| `data/` | programs, schedules, plans, curated examples |
| `src/school_program_intelligence/program` | schema, loaders, MSBA-inspired rules |
| `src/school_program_intelligence/spatial` | graph, visibility, space syntax, routing |
| `src/school_program_intelligence/temporal` | schedule, transitions, utilization |
| `src/school_program_intelligence/evaluation` | capacity, adjacency, circulation, scoring, diagnosis |
| `src/school_program_intelligence/optimization` | constraints, assignment, alternatives |
| `src/school_program_intelligence/llm` | priority interpreter + explanations only (deferred) |
| `app/` | plan / bubble / timeline / comparison UI |
| `tests/` | unit + fixture-based evaluation tests |

## Technical direction (provisional)

| Layer | Likely stack |
|-------|----------------|
| Backend | Python |
| Graphs / routing | NetworkX (or equivalent) |
| Optimization (later) | OR-Tools CP-SAT |
| Spatial metrics | custom + Space Syntax / VGA methods |
| UI | web app; optional Rhino/Grasshopper bridge later |
| Geometry I/O MVP | simplified 2D (polygons, doors, corridor graph) — not full BIM |

## Phased roadmap (build order)

### Phase 0 — Setup (this step)

- [x] Local folder scaffold  
- [x] README + `.gitignore`  
- [x] Public GitHub remote (`UsernameIsJoe/school-program-intelligence`)  
- [x] License (MIT)

### Phase 1 — Executable program (first real code)

Data model only: Program, Schedule, Relationships, Floor Plan fixtures.

**Done when:** tool can say whether a scheme supports the intended educational program (presence, area, capacity, basic relationships).

### Phase 2 — Scheme evaluation

Spatial graph, basic Space Syntax metrics, scheduled movement, utilization, A/B/C/D comparison dashboard.

**Done when:** convincing, metric-backed explanation of why Scheme A ≠ Scheme B.

### Phase 3 — Diagnosis

Rule- and metric-based issue list (travel, visibility, conflicts, bottlenecks).

### Phase 4 — Local optimization

Swaps / moves / small connections under constraints; preserve architectural intent.

### Phase 5+ — Broader search, light ABM, post-occupancy calibration

Deferred until scheme comparison proves useful.

## MVP scope (from README §19)

**In:** one simplified floor plan, ~20–40 programs, one school-day schedule, MSBA-inspired targets, adjacency prefs, priorities, route distance, weighted adjacency, corridor load, basic VGA/visual connectivity, utilization timeline, diagnosis + plain-language explanations + local suggestions.

**Out:** full ABM, high-fidelity BIM, code/MEP/structure, full geometry generation, construction cost.

## GitHub / local workflow

- Local path: `C:\Users\tu\Desktop\School programming`  
- Suggested remote name: `school-program-intelligence`  
- Visibility: **public**  
- Push: when requested

## Locked build decisions

1. Repo: `UsernameIsJoe/school-program-intelligence` (public)  
2. License: MIT  
3. Engines-first Python package + CLI; thin web UI after comparison is credible  
4. First fixture: synthetic toy elementary (`data/examples/toy_elementary/`)  
5. UI: FastAPI thin analytical views under `app/`
