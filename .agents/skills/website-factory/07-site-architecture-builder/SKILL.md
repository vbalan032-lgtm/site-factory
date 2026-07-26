---
name: 07-site-architecture-builder
description: Build and review project site architecture, routes, navigation, SEO clusters, GEO intent, internal links, and page priorities.
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# 07-site-architecture-builder

## Purpose
Keep the public site structured around conversion, trust, primary-offer demand, and portfolio expansion without confusing buyers or search systems.

## Inputs
- `PROJECT_MASTER_CONTEXT.md`
- `docs/SITEMAP_V1.md`
- `docs/PRODUCT_MAP.md`
- `docs/PERSONAS.md`
- `docs/CLAIMS_AND_PROOFS.md`
- Existing route files and navigation components when implementation is involved

## Workflow
1. Load source-of-truth context and current sitemap.
2. Map page role, audience, intent, parent/child relationships, and primary CTA.
3. Define internal links and navigation exposure.
4. Separate SEO intent from GEO answer-engine intent.
5. Flag missing proof, duplicate intent, cannibalization, or route ambiguity.

## Outputs
- Updated sitemap, route plan, navigation plan, or internal-linking notes.
- Page priority and dependency recommendations.

## Rules
- Do not create routes that blur configured primary offer with unrelated services.
- Do not invent pages without funnel, SEO, or trust purpose.
- Keep GEO meaning as generative engine optimization unless geography is explicit.
- Keep production release behind human approval.

