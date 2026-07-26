---
name: 02-creative-blueprint
description: Use when a contract-ready project page needs one approved full-page visual, UX, reference, topology, responsive, and implementation direction before copy or build work.
---

## Context entry

Use `shared/context-pack-loader` stdout JSON first. Read sources only via `exact_source_triggers`, changed fingerprints/conflicts, or an explicit cross-cutting audit. Never create tracked `CONTEXT_PACK.md`.

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# Creative Blueprint

Create one coherent `CREATIVE_BLUEPRINT.md` for the complete page. Combine the strongest former visual brief, UX strategy, implementation topology, and block-reference practices without creating block tasks.

## Inputs

- Valid `PAGE_CONTRACT.md` with current source fingerprints.
- Current implementation and screenshots when they exist.
- Design system and visual baseline as evidence, not an absolute ceiling.

## Workflow

1. If the page introduces a new archetype or major concept, use `superpowers:brainstorming` before committing to a direction.
2. Research 8-12 archetype references for a new archetype and 3-6 delta references for this page. Record source, useful pattern, anti-copy note, and relevance.
3. Let `design-taste-frontend` lead marketing-page composition. Use `ui-ux-pro-max` only for a new archetype, material redesign, or named UX/design uncertainty. Use `shadcn` project/component context only to check feasibility and reusable primitive coverage.
4. Define visual thesis, narrative sequence, section topology, visual anchor, and first-glance takeaway for every section.
5. Create a section-rhythm matrix that names each section's layout family, silhouette, reading direction, visual anchor, density, and mobile transformation. On pages with eight or more sections, use at least five visibly distinct layout families; never repeat a family in adjacent sections; use a generic equal-card grid at most once unless the domain content explicitly requires it. Headings, background tones, borders, and card styling alone do not count as different families. Specify conversion path, objections, responsive behavior, accessibility intent, motion, and asset needs.
6. Record every material deviation from the visual baseline: change, expected improvement, risk, and brand bridge.
7. Use Playwright only when a live/local route or interactive reference behavior cannot be judged reliably from static evidence.
8. Write `CREATIVE_BLUEPRINT.md` from `references/creative-blueprint-template.md`. After approval, run `scripts/validate_stage.py <CREATIVE_BLUEPRINT.md> --input <PAGE_CONTRACT.md>`; drafts cannot pass completion.

## Approval gate

Stop after presenting the complete direction and material deviations. Status changes to `creative_approved` only after explicit creative approval. Creative approval does not authorize copy changes, frontend changes, remote Git, staging, or production.

## Handoff

Provide section-level meaning and implementation topology, not separate section owners or statuses. Existing components remain evidence and may be revised later only when the approved full-page direction is demonstrably stronger.

The Blueprint fails if its full-page outline would still read as a sequence of similar heading-plus-panel blocks at thumbnail scale. Distinctness must survive both desktop composition and mobile collapse.
