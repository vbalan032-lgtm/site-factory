---
name: knowledge-graph-router
description: Use when a factory stage needs compact graph-first project context, dependency discovery, source impact analysis, or a safe filesystem fallback from Graphify without changing canonical files or lifecycle state.
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# Knowledge Graph Router

Use canonical files as truth and Graphify only as a derived context index.

## Workflow

1. Load and validate the project `GRAPH_PROFILE.json` with `scripts/graph_profile.py`.
2. Build exact artifact/lifecycle records with `scripts/factory_catalog.py`; semantic extraction cannot override them. Update materializes only profile-allowed files into generated staging and merges these records into the published graph.
3. Query through `scripts/query_context.py`, always scoped by `project_id`, stage and token budget.
4. Enforce the profile stage budget even when a caller requests more. Accept current `EXTRACTED` evidence before `INFERRED`; exclude `AMBIGUOUS` unless an explicit diagnostic asks for it.
5. Read exact allowlisted canonical files for Claim, Approval, Conflict, changed fingerprints and ReleaseEvidence. Reject a sensitive summary whose source is outside the allowlist.
6. On absent, stale, corrupt, cross-project or unavailable graph results, use the stage filesystem allowlist. Preserve page state.

Read `references/base-ontology.md` when adding node or edge types. Read `references/graph-profile-schema.md` when creating or migrating a project profile.

Queries and filesystem fallback are read-only and never trigger an update. Run an update only for an explicit owner request or a configured event trigger, and only through `scripts/update_graph.py`. Do not start watch, MCP, remote databases, hooks or visualization as part of normal stage work. Never treat graph evidence as authority for claims, approvals, Git, staging or production.
