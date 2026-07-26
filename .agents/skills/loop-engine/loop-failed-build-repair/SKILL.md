---
name: loop-failed-build-repair
description: Repair the smallest failed project build, CI, lint, typecheck, test, or merge-conflict state before page work resumes.
---

## Context entry

Use `shared/context-pack-loader` stdout JSON first. Read sources only via `exact_source_triggers`, changed fingerprints/conflicts, or an explicit cross-cutting audit. Never create tracked `CONTEXT_PACK.md`.

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# Failed Build Repair

## Workflow

1. Confirm compact `NEXT_TASK.md` selects `stage: repair` and this owner.
2. Reproduce the exact failing command or inspect authoritative CI/conflict evidence.
3. Diagnose and fix only the cause; do not add page, copy, claims, design, SEO/GEO, or release scope.
4. Rerun the failed check first and required adjacent gates second.
5. Clear only the separate blocker after evidence passes; preserve page lifecycle.
6. Hand results to `loop-status-updater` and `loop-report-builder`.

Do not commit, push, merge, close PRs, or deploy. If repair needs product/brand/claim judgment, competing conflict resolution, secrets, or broad refactor, stop with a blocker.
