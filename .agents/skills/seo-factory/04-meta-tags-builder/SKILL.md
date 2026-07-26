---
name: 04-meta-tags-builder
description: "Write, review, and implement project page meta tags and social metadata: title, description, OpenGraph, Twitter/X cards when used, canonical URL, robots meta, and alt text for key images. Use after a page SEO brief exists or when Codex needs to add, fix, or audit metadata in route files without changing schema JSON-LD or page body copy beyond image alt text."
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# 04-meta-tags-builder

## Purpose
Create and implement accurate metadata for one project page or article so search snippets, social previews, canonical signals, robots behavior, and key image alt text match the page intent and proof constraints.

This skill handles meta tags and image alt text. Use `seo-factory/06-schema-builder` for structured data and JSON-LD.

## Inputs
- `docs/pages/<slug>/SEO_BRIEF.md` or `docs/seo/briefs/<slug>.md`
- `docs/seo/KEYWORD_MAP.md`
- `docs/SITEMAP_V1.md`
- `docs/PRODUCT_MAP.md`
- `docs/PERSONAS.md`
- `docs/CLAIMS_AND_PROOFS.md`
- `docs/BRAND_STYLE.md`
- Target route/page files and existing metadata implementation
- Key image files, image components, alt attributes, and OpenGraph image assets
- Local Next.js docs in `node_modules/next/dist/docs/` before changing Next metadata APIs

## Workflow
1. Identify the target route, page type, canonical URL, indexability state, and primary search intent.
2. Read the SEO brief if present. If no brief exists, load keyword map, sitemap, product, persona, and claims context before drafting metadata.
3. Inspect current metadata implementation patterns in the repo before editing.
4. Draft or update:
   - `title`;
   - `description`;
   - OpenGraph title, description, URL, type, image, and image alt;
   - Twitter/X card fields only when the project already uses them or the task explicitly requests them;
   - canonical URL;
   - robots meta or framework robots settings;
   - alt text for key meaningful images.
5. Validate every claim against `docs/CLAIMS_AND_PROOFS.md`.
6. Implement metadata using the existing project pattern and current framework API.
7. Check rendered metadata when feasible with build, route inspection, browser, or static review.
8. Report changed fields, files, checks, and any residual proof or asset gaps.

## Outputs
- Implemented metadata changes in route/page files, metadata config, or content config.
- Updated alt text for key meaningful images.
- Optional `docs/pages/<slug>/META_TAGS_REPORT.md` when the task needs an audit trail.

Use this report shape when writing a report:

```markdown
# META_TAGS_REPORT: <route>

## Source Inputs
- SEO brief:
- Keyword map:
- Page files:

## Implemented Fields
- Title:
- Description:
- OpenGraph:
- Twitter/X:
- Canonical:
- Robots:
- Key image alt:

## Claims And Proof
- Supported:
- Needs proof:
- Removed or softened:

## Checks
- Commands:
- Rendered metadata check:
- Remaining risks:
```

## Field Rules
- Title must be specific to the page and usually include project only when useful for brand or navigational clarity.
- Description must state the page value clearly without unsupported performance promises.
- OpenGraph must reflect visible page content and use approved or existing image assets.
- Twitter/X cards are optional; add them only when the project uses them or the user asks.
- Canonical must match the intended indexable URL from the sitemap.
- Robots meta must not accidentally block launch-critical pages.
- Alt text must describe meaningful images concretely. Decorative images should remain decorative according to the frontend pattern.

## project Metadata Rules
- Keep project framed as the positioning defined in configured business sources.
- Keep configured primary offer as the entry offer where relevant.
- Treat the configured offer portfolio and growth path: configured secondary offers and integrations.
- Use controlled, precise, evidence-confident language.
- Do not use positioning prohibited by the configured brand rules.
- Do not create guaranteed ROI, guaranteed audit pass, full engineer replacement, best/only claims, fake awards, fake ratings, or unsupported certifications.

## Implementation Rules
- Do not change page body copy except key image alt text unless the user explicitly asks.
- Do not implement JSON-LD/schema here; hand that to `seo-factory/06-schema-builder`.
- Do not overwrite unrelated metadata for sibling routes.
- Do not add new metadata libraries without stack approval.
- For Next.js, read local docs for the current project version before using metadata APIs.
- Production deploy requires human approval.
