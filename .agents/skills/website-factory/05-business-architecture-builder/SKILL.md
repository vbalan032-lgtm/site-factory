---
name: 05-business-architecture-builder
description: Build and audit project business architecture, offer logic, configured offer portfolio, funnel stages, commercial paths, and proof requirements.
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# 05-business-architecture-builder

## Purpose
Clarify how project grows from configured primary offer into a broader configured offer portfolio of configured secondary offers and integrations.

## Inputs
- `PROJECT_MASTER_CONTEXT.md`
- `docs/PRODUCT_MAP.md`
- `docs/PERSONAS.md`
- `docs/CLAIMS_AND_PROOFS.md`
- `docs/BUSINESS_ARCHITECTURE.md`
- `docs/source-index/README.md`
- Funnel, offer, pricing, pilot, demo, and implementation notes when present

## Workflow
1. Load source-index rules, master context, product map, personas, claims, and current business architecture when it exists.
2. If `docs/BUSINESS_ARCHITECTURE.md` is missing, generate it before downstream page work continues.
3. When generating the file, treat these existing documents as the approved analogs:
   - `PROJECT_MASTER_CONTEXT.md` for business formula, funnel, Growth Engine logic, tone, and constraints;
   - `docs/PRODUCT_MAP.md` for product hierarchy, configured primary-offer role, portfolio expansion, commercial formats;
   - `docs/PERSONAS.md` for buyer committee, objections, CTAs, and lead forms;
   - `docs/CLAIMS_AND_PROOFS.md` for safe claims, proof levels, prohibited statements, and metric constraints.
4. Separate configured primary offer entry offer from portfolio expansion offers.
5. Map buyer pains, objections, proof needs, funnel stages, CTAs, and next commercial actions.
6. Align pages, forms, SEO/GEO planning, and sales materials to funnel stage.
7. Mark unsupported economics or outcomes as proof gaps and keep strong numeric claims in `docs/CLAIMS_AND_PROOFS.md`.

## Outputs
- Created or updated `docs/BUSINESS_ARCHITECTURE.md`.
- Updated business architecture or offer map when requested.
- Funnel and CTA recommendations.
- Proof and objection-handling notes.

## Rules
- Do not promise guaranteed ROI, full engineer replacement, or audit success.
- Keep claims anchored in `docs/CLAIMS_AND_PROOFS.md`.
- Do not invent facts; derive business architecture only from approved source documents or `docs/source-index/`.
- Keep tone controlled, precise, and commercially sober.
- Do not reduce project to one single-offer tool without offer portfolio path.
- Production deploy requires human approval.
