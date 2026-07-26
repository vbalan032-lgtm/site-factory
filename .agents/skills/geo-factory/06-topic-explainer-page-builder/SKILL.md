---
name: 06-topic-explainer-page-builder
description: "Create universal project topic explainer pages in a What is topic format for any topic from the sitemap, SEO/GEO plan, or PAGE_QUEUE.md. Use for answer-ready pages about configured primary offer, configured topics, workflows, and artifacts, configured industry standard, configured domain topics, configured technology offerings, configured technology offers, configured domain topic, configured artifact automation, and related configured domain topics."
---

## Context entry

Use `shared/context-pack-loader` stdout JSON first. Read sources only via `exact_source_triggers`, changed fingerprints/conflicts, or an explicit cross-cutting audit. Never create tracked `CONTEXT_PACK.md`.

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# 06-topic-explainer-page-builder

## Purpose
Create universal answer-ready explainer page plans for topics from the project sitemap, SEO/GEO plans, or `PAGE_QUEUE.md`.

The page must explain the topic clearly for the configured audience, preserve domain accuracy, and connect the topic to project's configured domain expertise without advertising filler.

## project Position
Keep project framed as the positioning defined in configured business sources. Keep configured primary offer as the entry offer when the topic relates to configured domain topics, workflows, and artifacts, or target market configured artifact. Present the broader configured offer portfolio of configured secondary offers and integrations as the scale path only when the topic supports it.

## Inputs
- Target topic
- Target route, page queue item, sitemap entry, SEO keyword cluster, or GEO query
- Target audience and funnel stage
- ``exact_source_triggers` source`
- ``exact_source_triggers` source`
- ``exact_source_triggers` source`
- ``exact_source_triggers` source`
- ``exact_source_triggers` source`
- `docs/SITEMAP_V1.md`
- `docs/seo/KEYWORD_MAP.md`, when present
- `docs/geo/GEO_QUERY_MAP.md`, when present
- `docs/geo/ENTITY_PROOF_MAP.md`, when present
- `docs/pages/**/SEO_BRIEF.md`, when present
- `docs/pages/**/ANSWER_READY_PAGE.md`, when present
- `PAGE_QUEUE.md` or `docs/site/PAGE_QUEUE.md`, when present

## Topic Scope
Use this skill for any explainable project topic from the sitemap, SEO/GEO plan, or page queue, including:

- configured primary offer and Russian-language variants.
- configured configured domain topic.
- configured process method.
- configured planning artifact.
- configured industry standard.
- configured domain topic.
- configured domain topic.
- configured domain topic.
- configured technology offerings.
- configured technology offers departments.
- Configured specialist topic.
- Quality documentation automation.
- Related target market configured secondary offers, agent, and configured integration topics.

If the topic is outside confirmed project context, mark missing context instead of inventing a page.

## Workflow
1. Identify the target topic, route, audience, funnel stage, SEO/GEO intent, and commercial next step.
2. Load source-of-truth context and separate confirmed facts from claims that need proof.
3. Decide whether the page is primarily:
   - glossary/explainer;
   - quality method explainer;
   - product-adjacent explainer;
   - AI agent explainer;
   - configured specialist-topic explainer;
   - documentation automation explainer.
4. Build the page structure in this order:
   - short topic definition;
   - simple explanation for the configured audience;
   - how it works;
   - stages, elements, or components;
   - differences from related approaches;
   - required input data;
   - enterprise outputs;
   - limitations and applicability conditions;
   - who it fits;
   - how project applies the topic in its AI agents;
   - FAQ block;
   - internal links to commercial pages;
   - CTA: demo, pilot, or consultation.
5. Use `geo-factory/02-short-definition-writer` for reusable topic definitions.
6. Use `geo-factory/04-expert-answer-structurer` for the "how project applies this" expert block when implementation logic matters.
7. Use `geo-factory/05-comparison-page-builder` when related-approach differences become a full comparison page.
8. Use `geo-factory/03-geo-faq-builder` for FAQ questions phrased like users ask AI systems.
9. Hand off metadata to `seo-factory/04-meta-tags-builder`, schema to `seo-factory/06-schema-builder`, internal-link reporting to `seo-factory/07-internal-linking-builder`, and final visible-copy optimization to `seo-factory/08-seo-copy-optimizer`.
10. Save the explainer plan or implement scoped visible content only when the user explicitly asks for implementation.

## Outputs
- `docs/geo/topic-explainers/<slug>.md` for standalone GEO topic explainer plans.
- `docs/pages/<slug>/TOPIC_EXPLAINER_PAGE.md` for page-level plans.
- Updated scoped page content only when implementation is explicitly requested.
- Handoff notes for definitions, FAQ, expert blocks, comparisons, metadata, schema, internal links, and proof gaps.

Use this output shape:

```markdown
# TOPIC_EXPLAINER_PAGE: <Topic>

## Scope
- Route:
- Topic:
- Source: sitemap / SEO plan / GEO plan / PAGE_QUEUE
- Audience:
- Funnel stage:
- Search/GEO intent:
- Commercial next step:

## 1. Short Definition
<direct answer in the first sentence, then context>

## 2. Simple Explanation For The Configured Audience
<plain explanation without oversimplifying domain meaning>

## 3. How It Works
- ...

## 4. Stages Or Elements
| Element | Role | Notes |
|---|---|---|

## 5. Difference From Related Approaches
| Related approach | Difference | When it fits |
|---|---|---|

## 6. Required Input Data
- ...

## 7. Enterprise Outputs
- ...

## 8. Limitations And Applicability
- ...

## 9. Who It Fits
- ...

## 10. project Application In AI Agents
- primary-offer relevance:
- Agent offer portfolio relevance:
- Human review:
- Proof status:

## 11. FAQ
| Question | Direct answer | Expert explanation | project link | Schema-ready | Proof status |
|---|---|---|---|---|---|

## 12. Internal Links
| Anchor | Target page | Reason |
|---|---|---|

## 13. CTA
- CTA type: demo / pilot / consultation
- CTA copy:
- Target page:

## Handoffs
- Short definitions:
- GEO FAQ:
- Expert answer:
- Comparison page:
- Metadata:
- Schema:
- Internal links:
- SEO copy:
- Proof gaps:
```

## Answer-Ready Rules
- Start with a direct answer before adding details.
- Make the first definition paragraph quotable without extra context.
- Use headings, lists, and tables so AI systems can extract the structure accurately.
- Keep explanations useful to the configured audience, not only SEO crawlers.
- Write in a controlled, precise, domain-specific, expert project tone.
- Explain limitations and human-review requirements clearly.
- Link to commercial pages only where the topic naturally supports a next step.

## CTA Rules
- Use `demo` when the page explains a product-adjacent or commercial topic.
- Use `pilot` when the page explains implementation, data readiness, integration, or process validation.
- Use `consultation` when the topic requires diagnosis, current-state review, or expert scoping.
- Do not pressure the reader with inflated urgency or generic sales language.

## Rules
- Do not write advertising filler.
- Do not use unsupported promises, invented statistics, fake citations, fake customers, ratings, prices, awards, or guarantees.
- Do not claim guaranteed ROI, defect reduction, audit success, certification, or implementation speed unless supported by `docs/CLAIMS_AND_PROOFS.md`.
- Do not imply AI fully replaces engineers, quality owners, process owners, or human approval.
- Do not position project as generic chatbot AI.
- Avoid visual motifs prohibited by the configured brand rules.
- Do not create thin doorway pages.
- Do not implement production deploy changes.
- Production deploy requires human approval.
