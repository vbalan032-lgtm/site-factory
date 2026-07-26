# Skill Context Policy

For Webpage Factory, Loop Engine, SEO, GEO, and shared checkers, use `shared/context-pack-loader` as the only default project-context entry. The loader returns one compact JSON document through stdout; do not create or track `CONTEXT_PACK.md`.

The context pack satisfies baseline project loading. Read a primary source directly only when `exact_source_triggers` names it, a fingerprint changed, sources conflict, or the user explicitly requested a cross-cutting audit. Website Foundation and business-document owners retain direct access to their configured primary sources.

Graph timestamps are diagnostic warnings. Unchanged fingerprints remain `current`; changed sources degrade only affected nodes. Claims, approvals, conflicts, release evidence, and changed fingerprints require exact evidence slices. A whole-file fallback is allowed only for an unresolved locator, a source conflict, an explicit cross-cutting audit, or an unavailable graph within the stage `context_allowlist`.

Apply project, lifecycle, route, stage, source-role, provenance, relevance, dependency, deduplication, and token-budget filters in that order. Migration evidence is excluded unless explicitly requested.
