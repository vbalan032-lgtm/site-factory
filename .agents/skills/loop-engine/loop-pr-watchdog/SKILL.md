---
name: loop-pr-watchdog
description: Monitor project PR, CI, review, conflict, QA, staging, and approval evidence without fixing, merging, or deploying.
---

## Context entry

Use `shared/context-pack-loader` stdout JSON first. Read sources only via `exact_source_triggers`, changed fingerprints/conflicts, or an explicit cross-cutting audit. Never create tracked `CONTEXT_PACK.md`.

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# PR Watchdog

Check available remote PR evidence or the local `PR_QUEUE.md`, then classify CI, reviews, conflicts, QA, staging, and owner approval. Update only PR evidence/reporting unless a failed CI or conflict must preempt page work.

When repair is required, write the compact six-field `NEXT_TASK.md` using:

```markdown
# NEXT_TASK

- page: <affected page>
- stage: repair
- owner: loop-engine/loop-failed-build-repair
- approval: not_required
- inputs: ["docs/release/PR_QUEUE.md", "<CI or conflict evidence>"]
- output: docs/system/FAILED_BUILD_REPAIR_REPORT.md
```

Never fix errors, merge, deploy, close PRs, or bypass approval. Missing remote integration is not fatal for a local non-release task, but unknown release-bound CI/review state blocks release decisions.
