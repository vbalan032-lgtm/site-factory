---
name: 02-task-state-manager
description: Maintain project canonical page lifecycle, separate blockers and approvals, compact next-task selection, and append-only history.
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# Task State Manager

## State ownership

- `PAGE_QUEUE.md`: only canonical page lifecycle.
- `NEXT_TASK.md`: one compact six-field operation.
- `STATUS.md`: generated Russian dashboard, never a source of truth.
- `LOOP_LOG.md`: compact append-only history.
- `PR_QUEUE.md`: remote PR evidence.
- `GRAPH_STATUS.json`: derived graph health only.

## Workflow

1. Parse canonical queue and task.
2. Keep blocker, approval, and growth iteration separate from lifecycle.
3. Require owning artifact validation and `validate_transition` before lifecycle mutation.
4. Prepare all dependent state outputs before replacing any target.
5. Preserve existing notes and history; append one concise Russian log entry.

## Rules

- Use only the v3 lifecycle from `STATUS_MODEL.md`.
- Never create block/section production statuses.
- Never mark incomplete or invalid work complete.
- Graph failure may add a warning but cannot roll back a valid artifact.
- Production remains explicitly approved and externally confirmed.
