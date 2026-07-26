---
name: 04-design-system-builder
description: Use when the project foundation needs a new or materially evolved design system, tokens, visual language, or reusable component rules.
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# 04-design-system-builder

## Purpose
Build a controlled, precise, evidence-confident design system for project pages, with configured primary offer documents, process flows, tables, proof blocks, and configured offer-portfolio visuals.

## Inputs
- `PROJECT_MASTER_CONTEXT.md`
- `docs/BRAND_STYLE.md`
- `docs/PRODUCT_MAP.md`
- `docs/CLAIMS_AND_PROOFS.md`
- Existing components, tokens, CSS, Tailwind config, and visual assets
- `docs/DESIGN_SYSTEM.md` and `docs/COMPONENT_LIBRARY.md`, when present

## Workflow
1. Load immutable brand rules and the evolvable visual baseline.
2. Use `ui-ux-pro-max` comprehensive research once for a new foundation or genuinely new direction.
3. Use `design-taste-frontend` to challenge generic marketing aesthetics.
4. Use `shadcn` as the primary authority for semantic tokens, reusable primitives, composition, project settings, and component contracts.
5. Reconcile findings against accessibility and implementation constraints; record deliberate customizations.

## Outputs
- Updated design-system documentation or implementation notes.
- Token/component recommendations.
- Visual QA risks and required checks.

## Rules
- Use restrained domain-specific visuals, not hype aesthetics.
- Avoid motifs and claims prohibited by the configured brand rules.
- Keep UI precise, dense where useful, and readable on mobile.
- Use approved accents and proof-led visuals.
- Production deploy requires human approval.
- This foundation skill does not own page production.
