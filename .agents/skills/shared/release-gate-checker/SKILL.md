---
name: release-gate-checker
description: "Use when QA-approved project work needs a scoped readiness verdict before staging, production approval, or a growth release step."
---

## Context entry

Use `shared/context-pack-loader` stdout JSON first. Read sources only via `exact_source_triggers`, changed fingerprints/conflicts, or an explicit cross-cutting audit. Never create tracked `CONTEXT_PACK.md`.

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# release-gate-checker

## Purpose
Decide whether a completed project task can move to the next release step. This skill only checks readiness; it does not perform release work, manage Git, or deploy.

## Inputs
- Task scope and changed files.
- QA reports and validation command output.
- Build, lint, typecheck, test, SEO, accessibility, visual, and browser check evidence when applicable.
- `docs/TECH_STACK.md`.
- `docs/CODEX_ENVIRONMENT.md`.
- Release notes, staging notes, rollback notes, or PR notes when present.

## Workflow
1. Identify release scope and next step: continue QA, prepare PR, staging handoff, or production approval.
2. Verify that required checks have evidence, not just intent.
3. Check changed files for secrets, environment risk, unrelated churn, or production-sensitive changes.
4. Confirm brand, claims, SEO/GEO, visual, accessibility, and responsive checks where applicable.
5. Classify result as `pass`, `pass_with_warnings`, or `fail`.
6. State whether human approval is required before the next step.

## Outputs
- Release gate report.
- Pass/fail status and blockers.
- Required next checks or approvals.

Use this report shape:

```markdown
# RELEASE_GATE_REPORT

## Scope
- Task:
- Changed files:
- Proposed next step:

## Evidence Reviewed
- ...

## Status
- Result: pass / pass_with_warnings / fail
- Can proceed:
- Human approval required:

## Blockers
- ...

## Warnings
- ...

## Required Next Actions
- ...
```

## Used Inside
- Stage 7 `release-growth`.
- `loop-pr-watchdog`.

Return release findings to Stage 7; do not perform or authorize the release.

## Rules
- Do not make commits, branches, PRs, pushes, pulls, releases, or deployments.
- Do not manage Git state.
- Do not deploy to staging or production.
- Do not claim readiness without evidence.
- Production deploy always requires explicit human approval.
