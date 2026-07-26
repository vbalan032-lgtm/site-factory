---
name: 05-full-page-build
description: Use when approved project page artifacts are ready for one coherent full-page frontend implementation and assembly.
---

## Context entry

Use `shared/context-pack-loader` stdout JSON first. Read sources only via `exact_source_triggers`, changed fingerprints/conflicts, or an explicit cross-cutting audit. Never create tracked `CONTEXT_PACK.md`.

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# Full-page Build

Implement and assemble the complete page in one run. Treat earlier components and blocks as migration evidence, not frozen output.

## Inputs

Read the validated `PAGE_CONTRACT.md`, approved `CREATIVE_BLUEPRINT.md`, `PAGE_COPY.md`, and `ASSET_MANIFEST.md` when present. Confirm Stage 4 ended as `assets_ready` or `assets_not_needed`.

Before changing Next.js code, read the relevant Next.js 16 guide under `node_modules/next/dist/docs/`. Use scoped Context7 only if local versioned docs do not answer a current library/API question. Load `docs/TECH_STACK.md` and only the code, design-system rules, and source files required by the build.

## Workflow

1. Inspect the route, shared components, data boundaries, styling, and existing tests. Preserve useful implementation while resolving it against the approved whole-page direction.
2. Build the full page and its responsive states as one narrative: hierarchy, section topology, adjacent-layout variety, CTA path, semantics, accessible interactions, forms, internal links, and assets. Implement the approved metadata, canonical URL, OpenGraph, schema, FAQ, and indexability requirements rather than leaving hooks for QA.
3. Inspect `shadcn` project context and component docs, then reuse stable primitives before custom interactive markup. Do not initialize or apply presets in this stage.
4. Apply only relevant `vercel-react-best-practices` rules to changed React/Next.js code, prioritizing waterfalls, bundles, server behavior, serialization, client boundaries, and rendering.
5. Keep public copy Russian and Cyrillic except accepted terms.
6. Use test-driven development for new behavior or bug fixes. Do not add tests that merely mirror implementation details.
7. Run scoped tests, lint, typecheck, and build. Record unrelated baseline failures precisely.
8. Use Playwright only as an advisory full-page smoke when a runnable page exists.
9. Create `BUILD_REPORT.md` from `references/build-report-template.md`, including implementation paths, reuse decisions, assets, commands and results, browser evidence, unresolved risks, and handoff status `built`.

Run `python scripts/validate_stage.py <BUILD_REPORT.md>` with repeated `--input` for the contract, blueprint, copy, and asset manifest when assets were required. Stop on unapproved concept or copy changes, unresolved claims, missing required assets, or failed build gates. Do not perform integrated QA or release here.
