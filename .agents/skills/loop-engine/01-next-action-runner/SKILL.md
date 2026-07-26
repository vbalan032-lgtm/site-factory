---
name: 01-next-action-runner
description: Execute exactly one selected project seven-stage page operation or repair from the compact NEXT_TASK contract.
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# Next Action Runner

## Inputs

- `docs/system/NEXT_TASK.md` with only `page`, `stage`, `owner`, `approval`, `inputs`, and `output`.
- `docs/site/PAGE_QUEUE.md`, `docs/system/QUEUE_CONTRACT.md`, and `docs/system/SKILL_CONTEXT_POLICY.md`.
- `docs/system/knowledge-graph/GRAPH_STATUS.json` when present.

## Workflow

1. Parse and validate the compact task with `.agents/skills/loop-engine/scripts/state_engine.py`.
2. Confirm task page and stage match canonical lifecycle selection.
3. Stop for failed build/CI, blocker, invalid input, or missing approval; use the selected repair owner when `stage: repair`.
4. For a page stage, load only its single `webpage-factory/01..07` owner, graph-first `context-pack-loader`, triggered specialists, and required handoff evidence.
5. Execute the complete-page stage once and run its validator.
6. Hand validated results to `loop-status-updater`; do not mutate lifecycle directly.
7. Stop after the selected stage and handoff report.

## Rules

- One action is one repair or one complete-page stage.
- Sections are implementation structure, never selected work units.
- A stale/unavailable graph uses filesystem fallback without changing the selected stage.
- Do not preload a skill family or use archived production routes.
- Do not commit, push, merge, stage, or deploy without explicit approval.
