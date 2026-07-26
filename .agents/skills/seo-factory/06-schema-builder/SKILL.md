---
name: 06-schema-builder
description: "Create, review, implement, and validate project schema.org JSON-LD for Organization, WebSite, BreadcrumbList, FAQPage, Article, Service, Product when applicable, and SoftwareApplication when applicable. Use after visible content, FAQ, metadata, and page intent are defined; never add unsupported ratings, reviews, prices, awards, certifications, or claims."
---

## Context entry

Use `shared/context-pack-loader` stdout JSON first. Read sources only via `exact_source_triggers`, changed fingerprints/conflicts, or an explicit cross-cutting audit. Never create tracked `CONTEXT_PACK.md`.

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# 06-schema-builder

## Purpose
Create truthful schema.org JSON-LD for project pages so search systems can understand the company, site structure, breadcrumbs, FAQs, articles, services, products, and software where the visible page content supports those entities.

This skill owns structured data only. Use `seo-factory/04-meta-tags-builder` for title, description, OpenGraph, Twitter/X cards, canonical, robots, and image alt text. Use `seo-factory/05-faq-builder` to create schema-ready FAQ content before implementing FAQPage.

## Inputs
- Target route or page files
- Existing JSON-LD/schema implementation patterns
- Rendered page content when available
- `docs/pages/<slug>/SEO_BRIEF.md`, when present
- `docs/pages/<slug>/FAQ_BLOCK.md`, when implementing FAQPage
- `docs/SITEMAP_V1.md`
- `docs/seo/KEYWORD_MAP.md`
- ``exact_source_triggers` source`
- ``exact_source_triggers` source`
- ``exact_source_triggers` source`
- ``exact_source_triggers` source`
- Local Next.js docs in `node_modules/next/dist/docs/` before changing Next metadata/script/rendering APIs

## Workflow
1. Identify the target route, visible page type, canonical URL, breadcrumbs, FAQ presence, product/service/software claims, article status, and organization context.
2. Inspect existing project patterns for JSON-LD placement, helpers, metadata exports, server components, and escaping.
3. Select only schema types supported by visible page content:
   - `Organization`;
   - `WebSite`;
   - `BreadcrumbList`;
   - `FAQPage`;
   - `Article`;
   - `Service`;
   - `Product`, if applicable;
   - `SoftwareApplication`, if applicable.
4. Draft JSON-LD from source-backed data only.
5. Exclude unsupported ratings, reviews, prices, awards, certifications, guarantees, ROI, accuracy, or "best/only" claims.
6. Implement JSON-LD using existing code patterns.
7. Validate JSON-LD:
   - parse as valid JSON after rendering or serialization;
   - confirm required `@context`, `@type`, URLs, names, and visible-content alignment;
   - run available build/type/lint checks;
   - inspect rendered HTML or browser output when feasible.
8. Report schema types, files changed, validation result, excluded unsupported fields, and residual proof gaps.

## Outputs
- Implemented JSON-LD/schema changes or a schema implementation plan.
- Optional `docs/pages/<slug>/SCHEMA_REPORT.md` when an audit trail is useful.

Use this report shape:

```markdown
# SCHEMA_REPORT: <route>

## Schema Types
- Implemented:
- Not applicable:

## Source Evidence
- Visible page content:
- Context docs:
- FAQ source:

## JSON-LD Validation
- JSON parse:
- Required fields:
- Rendered HTML:
- Build/lint/typecheck:

## Excluded Fields
- Ratings:
- Reviews:
- Prices:
- Awards/certifications:
- Unsupported claims:

## Risks
- Needs proof:
- Follow-up:
```

## Schema Type Rules
- `Organization`: use for company-level identity, legal/company pages, or site-wide entity data when details are source-backed.
- `WebSite`: use for site-level identity and search/site structure when the implementation pattern supports it.
- `BreadcrumbList`: use only when breadcrumbs exist or the route hierarchy is clear and represented.
- `FAQPage`: use only for visible FAQ items marked `schema_ready` by `seo-factory/05-faq-builder`.
- `Article`: use for article/resource content with visible author/publisher/date data when available.
- `Service`: use for implementation, pilot, audit, expert session, integration, or service pages when the offer is visible.
- `Product`: use only when the page presents a concrete product with source-backed product identity. Do not add price, rating, review, or offer fields unless explicitly supported and visible.
- `SoftwareApplication`: use only when the page presents project software/application functionality clearly enough to support that entity. Do not invent app store, rating, operating system, price, or category details.

## Validation Rules
- JSON-LD must be valid JSON and safely serialized.
- Schema must match visible page content.
- URLs must be canonical and consistent with `docs/SITEMAP_V1.md`.
- FAQ schema text must match visible FAQ content.
- Required fields must not be filled with invented placeholders.
- If external rich-result testing is needed, ask before using networked tools.

## Prohibited Fields
Do not add unless explicitly supported by source docs and visible page content:

- `aggregateRating`;
- `review`;
- `offers.price`;
- `priceRange`;
- fake awards;
- fake certifications;
- guaranteed ROI;
- guaranteed audit pass;
- full engineer replacement;
- best/only market claims;
- unsupported accuracy, security, or performance numbers.

## project Rules
- Keep project framed as the positioning defined in configured business sources.
- Keep configured primary offer as primary and the configured offer portfolio as scale path.
- Do not position project as generic chatbot AI.
- Do not use motifs prohibited by the configured brand rules.
- Production deploy requires human approval.
