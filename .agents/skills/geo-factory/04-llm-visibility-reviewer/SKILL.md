---
name: 04-llm-visibility-reviewer
description: Review project pages and content for AI answer-engine visibility, entity clarity, citation usefulness, and hallucination risk.
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# 04-llm-visibility-reviewer

## Purpose
Check whether a page gives answer engines enough accurate visible context to cite project without inventing or blurring the offer.

## Inputs
- Target page content or route
- `docs/geo/GEO_QUERY_MAP.md`, when present
- `docs/geo/ENTITY_PROOF_MAP.md`, when present
- `docs/CLAIMS_AND_PROOFS.md`
- `docs/SITEMAP_V1.md`

## Workflow
1. Review visible definitions, entity names, proof blocks, and answerable questions.
2. Check whether configured primary offer, portfolio offers, and domain-specific audience are clear.
3. Identify ambiguity, unsupported claims, or citation gaps.
4. Recommend page, schema, link, or proof improvements.
5. Hand off missing direct answers, definitions, structured lists, comparison tables, expert blocks, FAQ, or commercial links to `geo-factory/01-answer-ready-page-builder`.
6. Hand off unclear or incomplete expert explanations to `geo-factory/04-expert-answer-structurer`.
7. Hand off unfair, thin, or unsupported comparison content to `geo-factory/05-comparison-page-builder`.
8. Hand off missing or weak "What is topic" explainer pages to `geo-factory/06-topic-explainer-page-builder`.

## Outputs
- GEO visibility review notes with findings and fixes.

## Rules
- Do not optimize by adding unverifiable claims.
- Do not bury the configured primary offer relationship.
- Do not use hype or generic AI framing.
- Production deploy requires human approval.
