---
name: 03-quality-gate-runner
description: Run and record the exact validation gates required by one project repair or seven-stage page operation.
---

## Context entry

Use `shared/context-pack-loader` stdout JSON first. Read sources only via `exact_source_triggers`, changed fingerprints/conflicts, or an explicit cross-cutting audit. Never create tracked `CONTEXT_PACK.md`.

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# Quality Gate Runner

Identify checks from the selected owner stage and project commands, then record `pass`, `fail`, `skipped`, or `unavailable` without weakening requirements.

Page artifact validation precedes lifecycle transition. Stage 5 and Stage 6 may require lint, typecheck, build, browser, accessibility, SSR, performance, and responsive evidence. State-only work invokes no design/frontend tools. Failed build or CI produces repair evidence and preempts new page work.

Do not claim skipped checks passed, change lifecycle directly, create new scope, or bypass creative/production approval.
