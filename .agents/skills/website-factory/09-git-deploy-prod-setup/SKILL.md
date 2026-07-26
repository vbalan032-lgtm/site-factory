---
name: 09-git-deploy-prod-setup
description: Configure and audit project Git workflow, CI, staging, production guardrails, release notes, rollback, and deploy approval rules.
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# 09-git-deploy-prod-setup

## Purpose
Keep source control, CI/CD, staging, production, and rollback controlled enough for a configured-market site.

## Inputs
- `docs/TECH_STACK.md`
- `docs/CODEX_ENVIRONMENT.md`
- Git status, branches, remotes, CI files, package scripts, deployment notes
- `docs/SITEMAP_V1.md` and page QA reports for release scope

## Workflow
1. Inspect local Git state without reverting unrelated user changes.
2. Review branch, commit, PR, CI, staging, and production requirements.
3. Define validation gates before release.
4. Prepare release notes and rollback notes.
5. Stop before production deployment until human approval is explicit.

## Outputs
- Git/CI/deploy setup notes or config changes.
- Release checklist, staging handoff, and rollback notes.
- Clear approval gate for production.

## Rules
- Never store tokens in repo files or remote URLs.
- Ask before remote operations or meaningful commits.
- Do not deploy production automatically.
- Preserve staging before production and human approval before final release.
