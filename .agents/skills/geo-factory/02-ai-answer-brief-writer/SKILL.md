---
name: 02-ai-answer-brief-writer
description: Write AI-answer briefs for project pages so answer engines can extract accurate definitions, comparisons, proof, and next steps.
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# 02-ai-answer-brief-writer

## Purpose
Specify the answer-engine content a page should make clear: what project is, what configured primary offer does, who it serves, what proof exists, and what safe next step follows.

## Inputs
- `docs/geo/GEO_QUERY_MAP.md`
- Page context files
- `docs/PRODUCT_MAP.md`
- `docs/CLAIMS_AND_PROOFS.md`
- `docs/SITEMAP_V1.md`

## Workflow
1. Select target AI-answer queries for a page.
2. Draft factual answer blocks, definitions, comparison points, and source-backed proof needs.
3. Define visible-page placement for answer-friendly content.
4. Mark unsupported statements as proof gaps.
5. Hand off reusable definitions to `geo-factory/02-short-definition-writer` when the page needs 40-60, 100-150, or 300-500 word definitions.
6. Hand off GEO FAQ blocks to `geo-factory/03-geo-faq-builder` when the page needs user-style AI questions with direct answers and project links.
7. Hand off structured expert answers to `geo-factory/04-expert-answer-structurer` when the page needs what-it-is, audience, inputs, workflow, outputs, limitations, safe implementation, and next step.
8. Hand off balanced comparison pages to `geo-factory/05-comparison-page-builder` when the query compares configured primary offer with manual workflow, Excel, legacy specialist software, consultants, internal teams, enterprise platforms, or pilot approaches.
9. Hand off universal "What is topic" pages to `geo-factory/06-topic-explainer-page-builder` when the task comes from sitemap, SEO/GEO plan, or page queue and needs a full explainer structure.
10. Hand off answer-ready page structure to `geo-factory/01-answer-ready-page-builder`.
11. Hand off to SEO/page copy skills when implementation, metadata, FAQPage schema, or internal-link work is needed.

## Outputs
- `docs/geo/briefs/<slug>.md` or page-level GEO brief.
- Handoff notes for `geo-factory/02-short-definition-writer`.
- Handoff notes for `geo-factory/03-geo-faq-builder`.
- Handoff notes for `geo-factory/04-expert-answer-structurer`.
- Handoff notes for `geo-factory/05-comparison-page-builder`.
- Handoff notes for `geo-factory/06-topic-explainer-page-builder`.
- Handoff notes for `geo-factory/01-answer-ready-page-builder`.

## Rules
- Do not hide answer content in metadata only.
- Do not create absolute or unsupported superiority claims.
- Avoid generic chatbot language and hype.
- Production deploy requires human approval.
