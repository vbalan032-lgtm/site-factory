---
name: 04-handoff-reporter
description: Produce a concise Russian project handoff after one repair or complete-page stage with evidence, blockers, approvals, and the next safe stage.
---

## Context entry

Use `shared/context-pack-loader` stdout JSON first. Read sources only via `exact_source_triggers`, changed fingerprints/conflicts, or an explicit cross-cutting audit. Never create tracked `CONTEXT_PACK.md`.

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# Handoff Reporter

Report the selected page/stage, validated artifact, changed files, checks, graph state/fallback, blockers, approval requirement, and next canonical stage. Distinguish completed work from residual risk and skipped checks.

Do not hide failures, invent completion, mix the report with execution of another stage, or suggest production action without explicit approval.
