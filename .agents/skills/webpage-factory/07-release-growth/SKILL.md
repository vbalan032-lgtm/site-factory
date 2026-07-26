---
name: 07-release-growth
description: Use when a QA-approved project page needs staging preparation, an approved production release, or a traceable growth iteration.
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# Release + Growth

Run exactly one mode: `staging_prepare`, `production_release`, or `growth_iteration`. Preserve release history and approval boundaries.

## Inputs

Read `PAGE_QUEUE.md`, `NEXT_TASK.md`, `QA_REPORT.md`, rollback notes, and only the Git, CI, staging, analytics, or page artifacts required by the selected mode. Confirm fingerprints and current lifecycle state before changing it.

## Modes

### staging_prepare

Require `qa_passed`. Prepare the branch/commit/PR or equivalent staging package only within granted Git authority. Record checks, release notes, rollback target, staging location, and unresolved warnings. Use Playwright for a staging smoke check only when staging exists and browser evidence is useful. Advance to `staging_ready`; do not release production.

### production_release

Require `staging_ready`, current passing evidence, rollback readiness, and explicit production approval scoped to this page and release. Reconfirm the approval immediately before the external action. Release only through the approved project mechanism, verify the public route, record the release identifier and result, and advance to `released`. Stop rather than inferring missing authority.

### growth_iteration

Require a released page and a concrete evidence source such as analytics, search performance, research, support feedback, or an approved experiment. Preserve immutable release history, record the hypothesis and `iteration_stage`, and route the smallest justified change back to the appropriate earlier stage. Use `growth` only for active measured improvement, never as a substitute for QA or release.

Run `python scripts/validate_release_transition.py --mode <mode> --from-status <current> --to-status <target> --page-id <page> --route <route> --release-id <id> --repo-root <root>` with `--approval-file`, `--rollback`, `--history-file`, `--previous-history-size`, `--previous-history-sha256`, and `--iteration-stage` when required by the selected mode. The rollback evidence must be structured JSON scoped to the page and release. Prove append-only release history against canonical `docs/system/LOOP_LOG.md` by recording the size and SHA-256 of its previous byte prefix. Keep commit, remote Git, staging, and production as separate approval gates. Never include secrets in release artifacts, rewrite prior history, or bypass failed checks.
