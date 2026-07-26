---
name: loop-status-updater
description: Validate and atomically update project canonical page lifecycle, next task, generated Russian status, blockers, and append-only loop history.
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# Loop Status Updater

## Purpose

Apply one validated lifecycle transition while keeping queue, task, generated status, and log mutually consistent. This skill does not choose or execute page work.

## Inputs

- `docs/site/PAGE_QUEUE.md`.
- Compact `docs/system/NEXT_TASK.md`.
- The owning stage artifact and validator result.
- Scoped creative or production approval when required.
- Latest repair/PR result when updating a separate blocker.

## Workflow

1. Parse queue and task with `.agents/skills/loop-engine/scripts/state_engine.py`.
2. Validate the exact owning artifact, completion status, source fingerprints, language, and next-stage handoff.
3. Validate the lifecycle transition and approval scope.
4. On failure, preserve lifecycle and record the smallest separate blocker.
5. On success, prepare the next queue, task, Russian status, and one compact Russian log entry before writing any target.
6. Replace prepared files atomically; never hand-edit generated `STATUS.md`.
7. Request incremental graph update only after the validated state handoff. Graph failure changes only `GRAPH_STATUS.json` to `stale`.

## Lifecycle

```text
queued -> contract_ready -> creative_approved -> copy_ready
-> assets_ready | assets_not_needed -> built -> qa_passed
-> staging_ready -> released -> growth
```

Blocker and `iteration_stage` are separate fields. They never erase the last successful lifecycle status.

## Rules

- No transition before artifact validation.
- No `creative_approved` without scoped creative approval.
- No `released` without scoped production approval and confirmed production evidence.
- Never create section/block statuses.
- Never choose the next page or execute code/content work.
- Never commit, push, merge, or deploy.
