---
name: loop-report-builder
description: Build concise Russian owner reports for one project repair, complete-page stage, PR check, QA gate, release gate, or growth iteration.
---

## Context entry

Use `shared/context-pack-loader` stdout JSON first. Read sources only via `exact_source_triggers`, changed fingerprints/conflicts, or an explicit cross-cutting audit. Never create tracked `CONTEXT_PACK.md`.

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# Loop Report Builder

Read canonical queue, compact next task, generated status, append-only log, relevant QA/PR evidence, Git diff, and latest command results. Report only meaningful completed work, changed files, checks, graph state/fallback, blockers, approvals, risks, and the next safe stage.

Save daily/page/PR/failure/release reports under `docs/reports/` only when the selected task requires a persisted report. Keep `STATUS_SUMMARY.md` derived and Russian when updated.

Do not execute another stage, change product artifacts, hide failures, claim skipped checks passed, or imply production approval.
