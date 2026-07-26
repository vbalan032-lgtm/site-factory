---
name: factory-contracts
description: Validate project v3 page artifacts, source fingerprints, public Russian-language requirements, schemas, and stage handoffs without becoming the page owner or changing lifecycle state.
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# Factory Contracts

Use this shared specialist when a Webpage Factory stage or Loop Engine transition must validate a page artifact before changing canonical state.

## Scope

Validate only these page artifacts:

- `PAGE_CONTRACT.md`
- `CREATIVE_BLUEPRINT.md`
- `PAGE_COPY.md`
- conditional `ASSET_MANIFEST.md`
- `BUILD_REPORT.md`
- `QA_REPORT.md`

This skill does not write page strategy, copy, design, assets, frontend code, or lifecycle state. The owning Webpage Factory stage remains responsible for the artifact and corrections.

## Required workflow

1. Identify the expected artifact kind and owning stage.
2. Use `validate_artifact.py` only for schema/draft inspection. Before a state transition, run the owning stage's validator with every required `--input`; it enforces final status, current fingerprints, approvals, and handoff identity.
3. Return every schema, status, language, and handoff error to the owning stage.
4. Leave `PAGE_QUEUE.md`, `NEXT_TASK.md`, `STATUS.md`, and `LOOP_LOG.md` unchanged on failure.
5. On pass, return compact evidence that the Loop Engine can use for its separate transition check.

## Commands

```powershell
python .agents/skills/shared/factory-contracts/scripts/validate_artifact.py <artifact> --kind <KIND> --repo-root .
python .agents/skills/shared/factory-contracts/scripts/validate_skills.py .agents/skills
```

The first command validates artifact schema, not stage completion. Completion commands live under `.agents/skills/webpage-factory/<stage>/scripts/` and require the previous-stage artifact paths documented by that owner stage.

Allowed kinds:

- `PAGE_CONTRACT`
- `CREATIVE_BLUEPRINT`
- `PAGE_COPY`
- `ASSET_MANIFEST`
- `BUILD_REPORT`
- `QA_REPORT`

## Guardrails

- Use `.agents/skills` as the only active project skill root.
- Treat archived page/block artifacts as migration evidence, not normal inputs.
- Public copy must be Russian Cyrillic except accepted professional terms.
- Fingerprints use normalized repository-relative path, raw bytes, and schema version.
- Creative approval never satisfies production approval.
- Production, remote Git, and commits remain separate approval gates.
- Active skill names must be unique, and `.codex/skills` must contain no executable `SKILL.md`.

See `references/artifact-contracts.md` for the exact schemas and handoffs.
