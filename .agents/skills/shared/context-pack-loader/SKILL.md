---
name: context-pack-loader
description: Use when a project factory task needs a compact, stage-specific context pack without creating copy, design, code, business documents, or lifecycle state.
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# Context Pack Loader

Act as the project-level context router. Return only the trusted facts, constraints, fingerprints, and specialist triggers required by the current owner stage.

## Routing policy

1. Identify page, route, owner stage, expected output, and `context_allowlist` from `shared/factory-contracts/references/stage-context-policy.md`.
2. Use `knowledge-graph-router` first and call `route_context(...)` with project, stage, route, question, token budget, and the filesystem allowlist.
3. At Stage 1, use graph results for discovery and verify required business, claim, approval, and source evidence in exact files.
4. Accept only current same-project hits. Report graph freshness, provenance, evidence paths, confidence, source paths, and excluded stale or ambiguous hits.
5. Load claims, approvals, disputed facts, changed fingerprints, and release evidence from exact files. Graph summaries never replace those exact files.
6. If the graph is absent, stale, unhealthy, unsafe, or insufficient, fall back only to existing files in `context_allowlist` and record the reason.
7. At later stages, use an artifact-first policy for validated current page artifacts. Treat old page/block artifacts only as `migration_evidence` for migration or focused repair.
8. Apply the stage soft token budget and keep public website language Russian Cyrillic except approved technical and brand terms.

## Output

Return:

- page ID, route, stage, target output, and soft token budget;
- artifacts and sources used, with fingerprints;
- graph freshness, provenance, evidence paths, confidence, and fallback reason;
- relevant facts and hard constraints;
- claims/proof limits and Russian-language requirements;
- changed-source, conflict, and `migration_evidence` notes;
- unresolved items and approval gates;
- triggered SEO, GEO, claims, brand, design, accessibility, or technical advisers;
- minimal inputs for the next owner action.

Do not create or update source-of-truth documents, page artifacts, lifecycle state, copy, design, metadata, schema, or code. Do not invent missing facts. Keep project positioned as the positioning defined in configured business sources, configured primary offer as the entry offer, and the configured offer portfolio and growth path.
