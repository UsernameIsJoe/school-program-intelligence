# Setup & Development Plan

This document records setup and the **canonical app operation** for **School Program Intelligence**.

## Product in one line

Make the educational program **executable**: given program world **A**, spatial field **B**, and preference lens **C**, populate solutions, simulate them on A+B, and rank top candidates by C.

## Canonical operation (source of truth)

```text
A  Bubble diagram — programs, relationships, time-of-day schedule
B  Floor plan — configuration + per-space capacity, dimensions, availability
C  Preference prompt — open-ended definition of “good”

→ populate candidate solutions (program↔space on mostly fixed B)
→ simulate each against A + B
→ rate / select top candidates with C (prompt → editable weights → metrics)
→ show ranked schemes + diagnosis
```

Concepts stay aligned with the main [README](../../README.md) (MSBA, Space Syntax, temporal ops, diagnosis before generation, LLM interprets / engines measure). **Interaction is reorganized** around A/B/C — not around pre-baked scheme CLI scripts.

## Primary user & moment

- **Who:** architects (internal programming / DD), communicating with school stakeholders  
- **When:** building ~60–80% fixed; programs still movable  
- **Not:** generate a school from nothing

## Core principles

> Engines measure A×B. Prompt C only sets the ranking lens (visible weights).  
> Diagnosis from simulation accompanies ranked alternatives.  
> Search prefers assignment (and later small local moves) over radical redesign.

## Build direction (follow this, not legacy script UX)

| Track | Intent |
|-------|--------|
| **Author A** | Editable bubble + relationship + schedule input |
| **Author B** | Floor plan + space attribute editor / import |
| **Author C** | Preference prompt → editable priority weights |
| **Search** | Populate N candidates under fixed B |
| **Simulate** | Existing evaluation / temporal / spatial engines |
| **Select** | Rank by C; visual compare + diagnosis |

**Transitional:** `spi evaluate` / `compare` / toy fixture / current studio prove engines. Do not expand them as the primary product story; fold capabilities into the A→B→C→search loop.

## Repo layout

| Path | Role |
|------|------|
| `docs/` | research, MSBA notes, precedents, methodology |
| `data/` | programs, schedules, plans, curated examples |
| `src/school_program_intelligence/program` | schema, loaders |
| `src/school_program_intelligence/spatial` | graph, visibility, space syntax, routing |
| `src/school_program_intelligence/temporal` | schedule, transitions, utilization |
| `src/school_program_intelligence/evaluation` | capacity, adjacency, scoring, diagnosis |
| `src/school_program_intelligence/optimization` | assignment / local improvement search |
| `src/school_program_intelligence/llm` | priority interpretation (not metric invention) |
| `src/school_program_intelligence/web` | studio UI (evolve toward A/B/C authors) |
| `tests/` | unit + fixture tests |

## Locked decisions

1. Repo: `UsernameIsJoe/school-program-intelligence` (public)  
2. License: MIT  
3. Solutions v1: **program assignment** on fixed plan; small spatial moves later  
4. First fixture: `data/examples/toy_elementary/` (until A/B editors exist)  
5. C never fabricates analytical results

## GitHub / local

- Local: `C:\Users\tu\Desktop\School programming`  
- Remote: https://github.com/UsernameIsJoe/school-program-intelligence  
