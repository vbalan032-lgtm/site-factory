---
name: loop-daily-runner
description: "Run one safe project Loop Engine iteration: inspect PR/build state, select one seven-stage page operation, execute it, validate it, update state, and report."
---

## Context entry

Use `shared/context-pack-loader` stdout JSON first. Read sources only via `exact_source_triggers`, changed fingerprints/conflicts, or an explicit cross-cutting audit. Never create tracked `CONTEXT_PACK.md`.

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# Loop Daily Runner

## Purpose

Orchestrate one major task and stop. One run is either one repair or one complete-page Webpage Factory stage.

## Workflow

1. Use `loop-pr-watchdog` to classify open PR, CI, conflict, and approval state.
2. Use `loop-task-selector` to select exactly one operation from `PAGE_QUEUE.md`.
3. Read the compact six-field `NEXT_TASK.md`.
4. If `stage: repair`, use `loop-failed-build-repair` and stop after repair validation and reporting.
5. Otherwise load only the selected `webpage-factory/01..07` owner, `context-pack-loader` when context is needed, triggered specialists, and direct handoff contracts.
6. Execute one complete-page stage. Never split work into independently scheduled sections.
7. Validate the owning artifact before any lifecycle transition.
8. Use `loop-status-updater` for the atomic queue/task/status/log update.
9. After a validated macro-stage handoff, `update_knowledge_graph.py` may request one bounded incremental update. Graph failure records `stale` and cannot roll back a valid page artifact.
10. Use `loop-report-builder` and stop.

## Stop conditions

- Failed CI/build or merge conflict requires repair.
- Required input artifact is absent or invalid.
- Creative or production approval is missing for the requested transition.
- Selected work would require more than one page stage.
- Remote Git, staging, merge, or production action lacks explicit approval.

## Rules

- One run equals one repair or one complete-page stage plus state/report work.
- `PAGE_QUEUE.md` is canonical; `STATUS.md` is generated.
- Graph health never changes lifecycle selection.
- Preserve unrelated work and legacy artifacts until their selected migration task.
- Do not commit, push, merge, stage, or deploy without the applicable approval.
