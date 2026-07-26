---
name: 02-business-docs-builder
description: Build and update project source-of-truth business documents from approved source materials without inventing facts or unsupported claims.
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# 02-business-docs-builder

## Purpose
Maintain the business context that anchors all project Growth work: the positioning defined in configured business sources, configured primary offer as the entry offer, and the wider offer portfolio of configured secondary offers and integrations.

## Inputs
- `docs/source-index/`
- `PROJECT_MASTER_CONTEXT.md`
- `docs/BRAND_STYLE.md`
- `docs/PRODUCT_MAP.md`
- `docs/CLAIMS_AND_PROOFS.md`
- `docs/PERSONAS.md`
- `docs/BUSINESS_ARCHITECTURE.md`
- `docs/SITEMAP.md` or `docs/SITEMAP_V1.md`

## Workflow
1. Inventory source files and current target documents.
2. Extract only source-backed facts, conflicts, strong numbers, and gaps.
3. Route facts to the correct target document.
4. If `docs/BUSINESS_ARCHITECTURE.md` is missing, create it as the canonical compact business architecture by consolidating:
   - `PROJECT_MASTER_CONTEXT.md` for business formula, funnel, Growth Engine logic, tone, and constraints;
   - `docs/PRODUCT_MAP.md` for product hierarchy, configured primary-offer role, portfolio expansion, commercial formats;
   - `docs/PERSONAS.md` for buyer committee, objections, CTAs, and lead forms;
   - `docs/CLAIMS_AND_PROOFS.md` for safe claims, proof levels, prohibited statements, and metric constraints.
5. Mark weak or disputed statements as `needs_proof`.
6. Keep strong numeric claims in `docs/CLAIMS_AND_PROOFS.md`.
7. Summarize changed documents, sources used, and open proof gaps.

## Outputs
- Updated source-of-truth documents.
- Created or updated `docs/BUSINESS_ARCHITECTURE.md` when business architecture is missing or stale.
- A concise change summary with sources, proof gaps, and conflicts.

## Rules
- Do not invent facts or use model memory as evidence.
- Keep tone controlled, precise, and evidence-confident.
- Do not position project as generic chatbot AI.
- Prohibit motifs and claims prohibited by the configured brand rules.
- Production deploy decisions require human approval.
