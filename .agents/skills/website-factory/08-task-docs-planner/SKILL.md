---
name: 08-task-docs-planner
description: Use when project foundation work needs task contracts, queue seeds, dependencies, acceptance gates, rollback notes, or LOOP ENGINE-ready planning documents.
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# 08-task-docs-planner

## Purpose
Act as the foundation/task-contract maintainer. Define safe work and seed page demand without becoming a page-production owner.

## Inputs
- `PROJECT_MASTER_CONTEXT.md`
- `docs/TECH_STACK.md`
- `docs/CODEX_ENVIRONMENT.md`
- `docs/SITEMAP_V1.md`
- Relevant brand, product, persona, claims, SEO, and page docs
- `docs/system/QUEUE_CONTRACT.md`
- `docs/tasks/BACKLOG.md`, `docs/site/PAGE_QUEUE.md`, `docs/system/NEXT_TASK.md`, `docs/system/STATUS.md`, `docs/system/LOOP_LOG.md`, when present

## Workflow
1. Load source-of-truth context and existing task docs.
2. For new page work, seed `PAGE_QUEUE.md` with route, priority, dependencies, and evidence, then route production to `webpage-factory/01-page-contract`.
3. Split non-page work into atomic tasks with inputs, outputs, allowed files, dependencies, and checks.
4. Keep page work in `docs/site/PAGE_QUEUE.md`, non-page ready work in `docs/tasks/BACKLOG.md`, and exactly one selected task in `docs/system/NEXT_TASK.md`.
5. Record decisions, blockers, and rollback availability explicitly.
6. Update status after completion, blocking, or resequencing.

## Outputs
- LOOP ENGINE-ready task documents.
- Atomic tasks with acceptance criteria and quality gates.
- Status and decision updates.

## Rules
- Avoid vague tasks like "improve page" or "polish SEO".
- New page production starts at `webpage-factory/01-page-contract`; this skill never builds the page.
- `webblock-factory/*` is migration evidence/focused repair only.
- Preserve legacy skills. Rollback snapshot: `docs/system/skill-backups/webpage-factory-v1-2026-07-10/`.
- Do not schedule production deploy without human approval.
- Include required project context and review skills in each task.
- Preserve user-created task history unless it is explicitly superseded.
- Do not use or recreate `NEXT_ACTIONS.md` unless the owner explicitly changes the queue contract.
