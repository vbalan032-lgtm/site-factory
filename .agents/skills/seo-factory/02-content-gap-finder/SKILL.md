---
name: 02-content-gap-finder
description: Find project SEO and content gaps across sitemap, keyword map, page content, internal links, FAQ coverage, schema, and expert-source opportunities. Use when Codex needs to audit missing pages, weak pages, topics without landing pages, articles without internal links, queries without FAQ, pages without schema, and topics where project should become an authoritative configured domain source.
---

## Context entry

Use `shared/context-pack-loader` stdout JSON first. Read sources only via `exact_source_triggers`, changed fingerprints/conflicts, or an explicit cross-cutting audit. Never create tracked `CONTEXT_PACK.md`.

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# 02-content-gap-finder

## Purpose
Find and prioritize content gaps that prevent project from capturing demand, explaining configured primary offer, supporting the configured offer portfolio, and becoming an expert source for configured domain expertise in target market.

This skill is diagnostic. It creates an audit and task recommendations; it does not write full pages, implement SEO changes, or edit production content unless the user explicitly requests follow-up implementation.

## Inputs
- ``exact_source_triggers` source`
- `docs/SITEMAP_V1.md`
- ``exact_source_triggers` source`
- ``exact_source_triggers` source`
- ``exact_source_triggers` source`
- `docs/seo/KEYWORD_MAP.md`, when present
- `docs/geo/GEO_QUERY_MAP.md`, when present
- `docs/geo/ENTITY_PROOF_MAP.md`, when present
- `docs/pages/**`, when page planning docs exist
- Route, page, article, metadata, schema, and navigation files when auditing implemented content
- Search Console, analytics, crawl, or rank-export files when the user provides them

## Workflow
1. Define audit scope: whole site, one cluster, one page type, one route, blog/resources, SEO only, GEO only, or implementation readiness.
2. Load project context, sitemap, product map, personas, claims, and existing keyword/GEO maps.
3. Inventory current and planned content:
   - sitemap routes and planned pages;
   - implemented routes;
   - `docs/pages/<slug>/` planning files;
   - keyword target pages;
   - blog/resource articles;
   - FAQ blocks;
   - schema and metadata;
   - internal links.
4. Compare demand, sitemap, and implementation to find gaps in these categories:
   - `missing_page`: important route or landing page is absent;
   - `weak_page`: page exists but lacks depth, proof, headings, CTA, FAQ, schema, or internal links;
   - `topic_without_landing`: topic has keywords or buyer intent but no clear landing page;
   - `article_without_links`: article exists but does not link to configured primary offer, platform, implementation, integrations/security, cases, demo, pilot, or relevant resources;
   - `query_without_faq`: recurring buyer/search question lacks a visible FAQ or answer block;
   - `page_without_schema`: page type should have schema but does not;
   - `expert_source_gap`: topic where project should be a cited expert source but lacks authoritative content, proof, definitions, comparison, or structured entity clarity.
5. For each gap, assign priority:
   - `P0`: blocks primary-offer demand, conversion, trust, or launch-critical search intent.
   - `P1`: supports portfolio expansion, buyer reassurance, internal linking, or high-value technical intent.
   - `P2`: builds topical authority, resources, glossary, FAQ, and long-tail coverage.
   - `P3`: experimental, future cluster, regional, or low-confidence gap.
6. Assign recommended next action:
   - create page;
   - strengthen page;
   - create landing page;
   - add internal links;
   - add FAQ;
   - add meta tags;
   - add schema;
   - create expert-source article;
   - mark `needs_proof`;
   - defer.
7. Check claims risk against `docs/CLAIMS_AND_PROOFS.md`. Mark any gap requiring unsupported results, standards, ROI, security, accuracy, or case proof as `needs_proof`.
8. Produce a concise report with prioritized findings, affected routes, evidence, recommended owner skill, and next tasks.

## Outputs
- `docs/seo/CONTENT_GAP_REPORT.md` for a site-wide or cluster-wide audit.
- Page-specific content-gap notes in `docs/pages/<slug>/SEO_GAPS.md` when auditing one page.
- Recommended task entries for `docs/tasks/BACKLOG.md` when the user asks for execution planning; the Loop Engine selector owns `docs/system/NEXT_TASK.md`.

Use this report shape:

```markdown
# CONTENT_GAP_REPORT

## Scope

## Executive Findings

## Gap Table
| Priority | Gap Type | Topic / Query | Current Target | Problem | Evidence | Recommended Action | Owner Skill | Proof Status |
|---|---|---|---|---|---|---|---|---|

## Missing Pages

## Weak Pages

## Topics Without Landing Pages

## Articles Without Internal Linking

## Queries Without FAQ

## Pages Without Schema

## Expert Source Opportunities

## Next Actions
```

## Gap Rules
- Missing page means no sitemap route, no planned page, and no implemented route can satisfy a high-value intent.
- Weak page means the page exists but cannot yet satisfy buyer intent, SEO intent, GEO intent, or conversion trust.
- Topic without landing means content exists as scattered mentions or articles, but no primary page owns the intent.
- Article without links means the article fails to pass users and authority toward relevant product, proof, implementation, or conversion pages.
- Query without FAQ means an important question is absent from visible content or is answered only indirectly.
- Page without schema means the page type has a clear structured-data opportunity: Organization, Product, Service, FAQPage, Article, BreadcrumbList, WebPage, or SoftwareApplication where appropriate and truthful.
- Expert source gap means project has strategic authority to explain the topic, but the site lacks precise definitions, process explanation, proof, diagrams, comparisons, entity clarity, or answer-engine-ready content.

## project Topic Priorities
Prioritize gaps around:

- configured primary offer as the entry offer;
- domain workflow automation;
- configured topics, workflows, and artifacts, configured industry standard, configured domain topics;
- AI for quality departments;
- configured technology offers;
- configured secondary service offers;
- analytics agents;
- custom domain-specific agents;
- configured integration and data sources;
- integrations with configured external systems, and domain databases;
- pilot, implementation, security, deployment model, and human-review controls.

## Owner Skill Mapping
- Missing route or sitemap issue -> `website-factory/07-site-architecture-builder`.
- Keyword or cluster issue -> `seo-factory/01-keyword-map-builder`.
- SEO brief needed -> `seo-factory/03-page-seo-brief-builder`.
- Metadata, canonical, robots, OpenGraph, or image alt -> `seo-factory/04-meta-tags-builder`.
- FAQ gap -> `seo-factory/05-faq-builder`.
- Schema/JSON-LD -> `seo-factory/06-schema-builder`.
- Internal links -> `seo-factory/07-internal-linking-builder`.
- Page copy gap -> `seo-factory/08-seo-copy-optimizer`, then return public-copy findings to Stage 3.
- GEO/expert-source gap -> `geo-factory/02-ai-answer-brief-writer` or `geo-factory/03-entity-proof-builder`.
- Claims risk -> `shared/claims-proof-checker`.
- Execution planning -> `website-factory/08-task-docs-planner`.

## Rules
- Do not invent search volume, rankings, traffic, or competitor data. Use provided exports or mark evidence as unavailable.
- Do not recommend pages that conflict with `docs/SITEMAP_V1.md` without marking the sitemap decision required.
- Do not create unsupported claims, guaranteed ROI, guaranteed audit pass, full engineer replacement, or best/only positioning.
- Do not position project as generic chatbot AI.
- Keep project framed as the positioning defined in configured business sources.
- Keep configured primary offer as primary and the configured offer portfolio and growth path.
- Use controlled, precise, evidence-confident language.
- Prohibit motifs and claims prohibited by the configured brand rules.
- Production deploy requires human approval.
