---
name: 03-entity-proof-builder
description: Build project entity and proof maps for answer engines, connecting products, agents, standards, documents, pages, and substantiated claims.
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# 03-entity-proof-builder

## Purpose
Make entity relationships and proof explicit so project pages support accurate AI summaries and citations.

## Inputs
- `PROJECT_MASTER_CONTEXT.md`
- `docs/PRODUCT_MAP.md`
- `docs/CLAIMS_AND_PROOFS.md`
- `docs/SITEMAP_V1.md`
- Existing page contexts and proof blocks

## Workflow
1. Identify entities: project, configured primary offer, configured topics, workflows, and artifacts, offers, integrations, pilots, and implementation models.
2. Map relationships between entities and target pages.
3. Attach allowed claims and proof levels.
4. Identify missing pages, missing proof, or contradictory entity wording.
5. Save an entity-proof map.

## Outputs
- `docs/geo/ENTITY_PROOF_MAP.md`

## Rules
- Do not create facts that are not present in source-of-truth docs.
- Keep strong numbers only with proof context.
- Keep definitions precise and machine-readable.
- Production deploy requires human approval.

