---
name: 07-internal-linking-builder
description: "Build, implement, and report project internal linking between homepage, money pages, blog/resources, GEO pages, configured primary offer, configured topics, workflows, and artifacts, demo, pilot, integrations, and commercial pages. Use when Codex needs to plan or update internal links and produce docs/seo/INTERNAL_LINKING_REPORT.md."
---

## Context entry

Use `shared/context-pack-loader` stdout JSON first. Read sources only via `exact_source_triggers`, changed fingerprints/conflicts, or an explicit cross-cutting audit. Never create tracked `CONTEXT_PACK.md`.

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# 07-internal-linking-builder

## Purpose
Build internal linking that supports project conversion paths, topical authority, and answer-engine clarity without over-linking or using misleading anchors.

This skill may implement links in page, article, navigation, or content files when the user asks for updated links. It must always record the work in `docs/seo/INTERNAL_LINKING_REPORT.md`.

## Inputs
- ``exact_source_triggers` source`
- `docs/SITEMAP_V1.md`
- `docs/seo/KEYWORD_MAP.md`, when present
- `docs/seo/CONTENT_GAP_REPORT.md`, when present
- `docs/pages/**/SEO_BRIEF.md`, when present
- `docs/geo/GEO_QUERY_MAP.md`, when present
- `docs/geo/ENTITY_PROOF_MAP.md`, when present
- Existing route, blog/resource, navigation, and content files
- Current `docs/seo/INTERNAL_LINKING_REPORT.md`, when present
- Local Next.js docs in `node_modules/next/dist/docs/` before changing Next routing/link implementation patterns

## Workflow
1. Define scope: whole site, one route, one cluster, blog/resources, GEO pages, or launch-critical money pages.
2. Load sitemap, keyword map, page briefs, GEO maps, and existing content.
3. Inventory source and target pages:
   - homepage;
   - money pages;
   - configured primary-offer page;
   - blog/resource pages;
   - GEO pages;
   - configured topics, workflows, and artifacts pages or sections;
   - demo, pilot, implementation, integrations/security, and contact pages.
4. Build required link flows:
   - homepage -> money pages;
   - blog/resources -> configured primary offer;
   - GEO pages -> commercial pages;
   - related configured topic and workflow topics;
   - relevant pages -> demo, pilot, and integrations/security;
   - configured primary offer -> implementation, pilot, demo, integrations/security, proof/resources;
   - offer-portfolio pages -> configured primary offer when configured primary offer is the entry path.
5. Choose anchors that are descriptive, natural, and truthful.
6. Implement links only in scoped files and only where the link helps a reader or search system.
7. Check that target routes exist or are clearly planned. Mark missing targets instead of inventing routes.
8. Update `docs/seo/INTERNAL_LINKING_REPORT.md` with planned and implemented links, changed files, missing pages, and follow-up tasks.

## Outputs
- Updated internal links in scoped page, article, navigation, or content files.
- `docs/seo/INTERNAL_LINKING_REPORT.md`.

Use this report shape:

```markdown
# INTERNAL_LINKING_REPORT

## Scope
- Date:
- Routes/clusters:
- Files reviewed:

## Implemented Links
| Source | Target | Anchor | Link flow | File | Reason |
|---|---|---|---|---|---|

## Recommended Links Not Implemented
| Source | Target | Anchor | Reason not implemented | Owner skill |
|---|---|---|---|---|

## Required Link Flows
- Homepage -> money pages:
- Blog/resources -> configured primary offer:
- GEO pages -> commercial pages:
- configured topics, workflows, and artifacts cross-links:
- Demo/pilot/integrations links:

## Broken Or Missing Targets

## Risks And Notes
```

## Link Flow Rules
- Homepage must point users toward money pages and the configured primary offer path.
- Blog/resource articles must include useful links to configured primary offer or relevant commercial pages when the topic supports it.
- GEO pages must connect answer-engine/informational demand to commercial next steps.
- configured configured domain topic, configured process method, and configured planning artifact topics must cross-link where the relationship helps explain the configured workflow.
- Demo, pilot, implementation, and integrations/security pages must be reachable from pages where buyers evaluate next steps.
- Do not force links into unrelated paragraphs.

## Anchor Rules
- Use descriptive anchors such as `configured primary offer`, `configured workflow`, `configured process method and configured planning artifact`, `pilot project`, `integration and security`, or `request a demo`.
- Avoid vague anchors like `click here`, `learn more`, or repeated exact-match keyword stuffing.
- Do not use anchors that imply unsupported claims, guaranteed outcomes, or unavailable pages.
- Keep anchors readable in Russian or English according to the page language.
- If anchor wording requires broader copy rewriting, hand off visible copy optimization to `seo-factory/08-seo-copy-optimizer`.

## Implementation Rules
- Reuse existing link components and routing patterns.
- Do not create new routes as part of linking unless the user explicitly asks.
- Do not modify unrelated copy except small link-anchor adjustments needed for natural insertion.
- Do not add links to draft, blocked, noindex, or proof-missing pages unless the report marks the risk.
- For Next.js link/routing changes, read local project docs first.

## project Rules
- Keep project framed as the positioning defined in configured business sources.
- Keep configured primary offer as primary and the configured offer portfolio as scale path.
- Treat GEO as generative engine optimization unless geography is explicit.
- Do not position project as generic chatbot AI.
- Do not use motifs prohibited by the configured brand rules.
- Production deploy requires human approval.
