---
name: 06-integrated-qa-refinement
description: Use when a built project page needs integrated full-page critique, one refinement pass, and a release-readiness verdict.
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# Integrated QA + Refinement

Review the page as one complete experience, apply one coherent refine-pass, and issue the evidence-backed verdict in `QA_REPORT.md`.

## Inputs

Read all validated page artifacts and the implemented route. Load source documents again only for changed fingerprints, conflicting claims, thematic specialist triggers, or unresolved release risks.

## Workflow

1. Capture or inspect full-page desktop and mobile evidence. Use Playwright when repeatable screenshots, accessibility-tree inspection, interactions, overflow checks, or SEO/SSR browser evidence materially improves confidence; otherwise use lighter inspection.
2. For actual UI changes, fetch the current `web-design-guidelines` source and review only changed UI files. Accessibility, semantics, interaction, and compliance findings can block and outrank `design-taste-frontend` preferences.
3. Apply relevant `vercel-react-best-practices` and `shadcn` composition/token checks only to changed React/Next.js files. Use `design-taste-frontend` for full-page hierarchy, cohesion, conversion, section variety, and anti-slop critique. Audit the full-page render at normal size and thumbnail scale: assign every section a layout family, reject adjacent repetitions, and treat repeated heading-plus-white-panel silhouettes or generic card-grid dominance as a blocking defect. A long page with eight or more sections needs at least five visibly distinct families whose differences survive mobile collapse.
4. Compare baseline deviations against the approved Creative Blueprint and check Russian public copy.
5. Check claims/proof, accessibility, SEO/SSR, rendered metadata, links/forms, assets, performance, lint, typecheck, tests, and build; do not weaken tests or CI.
6. Consolidate duplicate findings by severity before one refine-pass; extra passes require a still-failing gate.
7. Re-run affected checks and refresh evidence after material changes.
8. Create `QA_REPORT.md`; set `qa_passed` only when release gates pass.

Run `python scripts/validate_stage.py <QA_REPORT.md>` with repeated `--input` for every required completed page artifact and the conditional asset manifest. Browser checks are advisory in method, but the report must contain sufficient evidence for every applicable gate. Do not stage, commit, push, or release from this stage.
