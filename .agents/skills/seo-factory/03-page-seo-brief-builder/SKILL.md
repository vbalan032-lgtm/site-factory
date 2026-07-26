---
name: 03-page-seo-brief-builder
description: Create project page SEO briefs with primary keyword, secondary keywords, search intent, title, description, H1, H2 structure, FAQ, schema type, internal links, content requirements, and proof requirements. Use when Codex needs a complete SEO brief before writing, assembling, optimizing, or enhancing a project page or article.
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# 03-page-seo-brief-builder

## Purpose
Create a complete, proof-aware SEO brief for one project page or article so downstream copy, page, schema, and internal-link work can be executed without guessing.

The brief must keep project positioned as the positioning defined in configured business sources, with configured primary offer as the entry offer and the broader configured offer portfolio and growth path.

## Inputs
- `PROJECT_MASTER_CONTEXT.md`
- `docs/SITEMAP_V1.md`
- `docs/PRODUCT_MAP.md`
- `docs/PERSONAS.md`
- `docs/CLAIMS_AND_PROOFS.md`
- `docs/seo/KEYWORD_MAP.md`
- `docs/seo/CONTENT_GAP_REPORT.md`, when the brief comes from a gap audit
- `docs/pages/<slug>/CONTEXT_PACK.md`, when present
- `docs/pages/<slug>/SITE_CONTEXT.md`, when present
- `docs/geo/GEO_QUERY_MAP.md`, when GEO/AI-answer visibility matters
- Existing page or route content when briefing an update

## Workflow
1. Identify the target page, route, topic, buyer audience, and funnel role.
2. Select one `primary keyword` that matches the page's main intent and does not cannibalize another page.
3. Select `secondary keywords` that support the same intent, including Russian and English variants when relevant.
4. Define `search intent`: commercial, informational, comparison, technical, navigational, or mixed with a dominant intent.
5. Draft SEO fields:
   - `title`;
   - `description`;
   - `H1`;
   - ordered `H2` structure;
   - FAQ questions and answer intent;
   - recommended schema type;
   - internal links in and out;
   - content requirements;
   - proof requirements.
6. Check claims and proof needs against `docs/CLAIMS_AND_PROOFS.md`.
7. Flag unsupported claims as `needs_proof` and rewrite strong claims into safe wording.
8. Save the brief to the expected output path.

## Outputs
- `docs/seo/briefs/<slug>.md` for standalone SEO briefs.
- `docs/pages/<slug>/SEO_BRIEF.md` for page-level briefs.

Use this structure:

```markdown
# SEO_BRIEF: <Page / Route>

## Page
- Route:
- Page type:
- Audience:
- Funnel role:

## Keywords
- Primary keyword:
- Secondary keywords:

## Search Intent
- Dominant intent:
- Secondary intent:
- User questions:

## Metadata
- Title:
- Description:

## Headings
- H1:
- H2:
  - ...

## FAQ
| Question | Answer intent | Proof needed | Target block |
|---|---|---|---|

## Schema
- Recommended schema type:
- Required properties:
- Do not use:

## Internal Links
- Incoming links:
- Outgoing links:
- Anchor recommendations:

## Content Requirements
- Required topics:
- Required examples or process details:
- Required visuals or tables:
- Required CTA:

## Proof Requirements
- Supported claims:
- Claims requiring proof:
- Prohibited claims:
- Safe wording:

## Handoff
- Body copy owner skill: `seo-factory/08-seo-copy-optimizer`
- Metadata owner skill: `seo-factory/04-meta-tags-builder`
- FAQ owner skill: `seo-factory/05-faq-builder`
- Schema owner skill: `seo-factory/06-schema-builder`
- Internal links owner skill: `seo-factory/07-internal-linking-builder`
- Implementation notes:
```

## Brief Rules
- One SEO brief equals one page, route, article, or landing page.
- One primary keyword per brief.
- Secondary keywords must support the same page intent, not create cannibalization.
- Visible body-copy optimization after the brief belongs to `seo-factory/08-seo-copy-optimizer`.
- FAQ must answer real buyer/search questions and should be created or refined with `seo-factory/05-faq-builder` when a dedicated FAQ block is needed.
- Metadata implementation belongs to `seo-factory/04-meta-tags-builder`.
- Schema implementation belongs to `seo-factory/06-schema-builder`.
- Internal-link architecture and implementation belong to `seo-factory/07-internal-linking-builder`.
- Schema type must match visible content and page type.
- Internal links must support buyer navigation and topical authority, not arbitrary cross-linking.
- Content requirements must specify what the page must explain, prove, compare, or convert.
- Proof requirements must name which claims are supported and which require proof.

## Schema Guidance
Use conservative schema recommendations:

- `WebPage` for general pages.
- `FAQPage` only when visible FAQ exists and `seo-factory/05-faq-builder` marks items as schema-ready.
- `Article` or `BlogPosting` for articles and resources.
- `BreadcrumbList` when breadcrumbs are present or planned.
- `Organization` for company-level pages.
- `Product`, `Service`, or `SoftwareApplication` only when the visible content truthfully supports that page type.

Do not recommend fake reviews, ratings, awards, certifications, aggregate ratings, or unsupported offer data.

## Internal Link Priorities
Prioritize links among:

- configured primary-offer page;
- platform and offer-portfolio pages;
- implementation and pilot pages;
- integrations and security pages;
- cases, proof, and resource pages;
- contacts, demo, or consultation CTAs.

## Rules
- Do not write the final page copy; create a brief for downstream work.
- Do not invent keyword volume, rankings, or search data.
- Do not create unsupported ROI, accuracy, certification, security, or best/only claims.
- Do not position project as generic chatbot AI.
- Keep language controlled, precise, and evidence-confident.
- Avoid visual motifs prohibited by the configured brand rules.
- Keep configured primary offer as primary and the configured offer portfolio as scale path.
- Production deploy requires human approval.
