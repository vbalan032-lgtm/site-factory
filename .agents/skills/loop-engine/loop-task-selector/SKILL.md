---
name: loop-task-selector
description: Select exactly one safe project page stage from the canonical seven-stage lifecycle while preserving repair, approval, and graph-fallback safety.
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# Loop Task Selector

## Purpose

Select one next operation from canonical page lifecycle evidence. This skill selects; it does not execute a page stage, mutate artifacts, commit, or deploy.

## Inputs

- `docs/site/PAGE_QUEUE.md` as the only canonical page lifecycle state.
- `docs/system/knowledge-graph/GRAPH_STATUS.json` as derived context health.
- `docs/release/PR_QUEUE.md`, CI/build evidence, and blockers.
- Current validated page artifacts and approvals when the lifecycle requires them.

## Selection order

1. Failed build, failed CI, merge conflict, or blocking PR repair.
2. The current active page and its lifecycle-mapped stage.
3. The highest-priority queued page when no page is active.
4. Release or growth work for a page already at Stage 7.

Normal lifecycle mapping is exact:

| Status | Stage |
|---|---|
| `queued` | `01-page-contract` |
| `contract_ready` | `02-creative-blueprint` |
| `creative_approved` | `03-conversion-copy` |
| `copy_ready` | `04-page-assets` |
| `assets_ready`, `assets_not_needed` | `05-full-page-build` |
| `built` | `06-integrated-qa-refinement` |
| `qa_passed`, `staging_ready`, `released`, `growth` | `07-release-growth` |

Use `.agents/skills/loop-engine/scripts/state_engine.py` as the executable mapping. A stale or unavailable graph never changes the selected page stage; it adds a filesystem-fallback warning. A changed fingerprint or disputed claim requires exact canonical source loading.

## Output

Write only this compact shape to `docs/system/NEXT_TASK.md`:

```markdown
# NEXT_TASK

- page:
- stage:
- owner:
- approval:
- inputs: []
- output:
```

For a failed build/CI/PR blocker, the same six fields may select `stage: repair` and owner `loop-engine/loop-failed-build-repair`. No business context, quality checklist, block status, or reasoning dump belongs in `NEXT_TASK.md`.

## Rules

- Select one page and one stage only.
- Never select a section or block as a factory task.
- Never route normal production to archived skills or Webblock Factory.
- Failed build/CI and blocking PR state preempt page work.
- Creative and production approvals remain explicit and scoped.
- Graph state is derived context health, not lifecycle and not a substitute for proof.
- Do not execute work, update lifecycle, commit, push, merge, or deploy.
