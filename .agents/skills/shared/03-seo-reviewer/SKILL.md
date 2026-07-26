---
name: 03-seo-reviewer
description: Use when a project copy package or implemented page needs scoped SEO, SSR/indexability, metadata, linking, schema, sitemap, robots, or search-visible-content review.
---

## Context entry

Use `shared/context-pack-loader` stdout JSON first. Read sources only via `exact_source_triggers`, changed fingerprints/conflicts, or an explicit cross-cutting audit. Never create tracked `CONTEXT_PACK.md`.

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# 03-seo-reviewer

## Purpose
Catch SEO regressions and search architecture issues before release.

## Inputs
- Target route or page files
- `docs/SITEMAP_V1.md`
- `docs/seo/KEYWORD_MAP.md`, when present
- Metadata/schema implementation
- Rendered HTML or browser output when available

## Workflow
1. Check sitemap fit, canonical, indexability, title, description, headings, and visible content.
2. Review internal links, alt text, schema, OpenGraph, and robots behavior.
3. Check claims and keyword usage for risk.
4. Report findings with file references and severity.

## Outputs
- SEO review findings and recommended fixes.
- Stage 3 owns content/metadata/SEO-GEO findings; Stage 6 owns implementation and rendered-page findings.
- Return findings to the owner stage without editing lifecycle state.

## Rules
- Do not accept hidden or metadata-only content as a substitute for useful page content.
- Do not approve keyword stuffing or unsupported claims.
- Keep configured primary offer and offer-portfolio pages linked coherently.
- Production deploy requires human approval.
