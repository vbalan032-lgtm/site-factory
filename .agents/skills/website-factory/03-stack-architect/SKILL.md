---
name: 03-stack-architect
description: Analyze and evolve the project website technical stack, repository structure, validation commands, environments, and deployment boundaries.
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# 03-stack-architect

## Purpose
Keep the project site stack practical, maintainable, and aligned with configured market trust: Next.js for the public site, clear quality gates, portable deployment, and no unnecessary services.

## Inputs
- `docs/TECH_STACK.md`
- `docs/CODEX_ENVIRONMENT.md`
- `PROJECT_MASTER_CONTEXT.md`
- `package.json`, config files, CI files, environment examples
- Local Next.js docs in `node_modules/next/dist/docs/` for Next-specific changes

## Workflow
1. Read stack and Codex environment docs before architecture decisions.
2. Inspect current project structure, scripts, config, and deployment notes.
3. Identify gaps, risks, and changes needed for the requested work.
4. Prefer existing stack patterns and minimal new dependencies.
5. Document recommended commands, file boundaries, and validation gates.

## Outputs
- Stack notes or updates to technical docs.
- A scoped implementation plan for infrastructure or architecture work.
- Validation commands and residual risks.

## Rules
- Do not add heavy services without a concrete role.
- Preserve Docker/on-prem portability and staging before production.
- Use Context7 only when local docs are insufficient.
- Keep project positioned as the positioning defined in configured business sources, not generic AI tooling.
- Production deploy requires human approval.

