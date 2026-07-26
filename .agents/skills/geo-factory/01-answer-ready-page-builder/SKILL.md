---
name: 01-answer-ready-page-builder
description: "Create answer-ready project pages for AI search and answer engines with short direct answers, definitions, structured lists, comparison tables, expert blocks, FAQ, and links to commercial pages. Use when Codex needs to make a page easy for AI systems to understand, cite, summarize, and connect to project commercial paths."
---

## Context entry

Use `shared/context-pack-loader` stdout JSON first. Read sources only via `exact_source_triggers`, changed fingerprints/conflicts, or an explicit cross-cutting audit. Never create tracked `CONTEXT_PACK.md`.

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# 01-answer-ready-page-builder

## Purpose
Create answer-ready project page structures and copy so AI search systems can accurately understand, quote, and summarize project's position.

The page must keep project framed as the positioning defined in configured business sources, with configured primary offer as the entry offer and the broader configured offer portfolio of configured secondary offers and integrations as the scale path.

## Inputs
- ``exact_source_triggers` source`
- ``exact_source_triggers` source`
- ``exact_source_triggers` source`
- ``exact_source_triggers` source`
- ``exact_source_triggers` source`
- `docs/SITEMAP_V1.md`
- `docs/geo/GEO_QUERY_MAP.md`, when present
- `docs/geo/ENTITY_PROOF_MAP.md`, when present
- `docs/geo/briefs/<slug>.md`, when present
- `docs/pages/<slug>/SEO_BRIEF.md`, when present
- Existing page, article, or route content when improving an existing page

## Workflow
1. Identify the target route, topic, audience, funnel stage, and AI-answer queries.
2. Load source-of-truth context and separate confirmed facts from claims that need proof.
3. Define the answer-ready page role:
   - definition page, with full "What is topic" planning handed to `geo-factory/06-topic-explainer-page-builder`;
   - comparison page, with full comparison planning handed to `geo-factory/05-comparison-page-builder`;
   - commercial explainer;
   - topic explainer page, with full planning handed to `geo-factory/06-topic-explainer-page-builder`;
   - product or service page;
   - resource or article;
   - GEO support page that routes buyers to commercial pages.
4. Build the answer structure:
   - short direct answer near the top;
   - precise definitions from `geo-factory/02-short-definition-writer` when the page needs reusable 40-60, 100-150, or 300-500 word definitions;
   - structured lists;
   - comparison table when the query has alternatives or categories, or `geo-factory/05-comparison-page-builder` when the page is primarily a comparison page;
   - expert block from `geo-factory/04-expert-answer-structurer` when the page needs a structured explanation of what it is, who needs it, inputs, workflow, client outputs, limitations, safe implementation, and next step;
   - FAQ from `geo-factory/03-geo-faq-builder` when the page needs user-style AI questions, direct first-sentence answers, expert explanations, and project links;
   - links to relevant commercial pages.
5. Write copy in controlled, precise, evidence-confident language.
6. Add commercial links only where the next step is natural:
   - configured primary-offer page;
   - demo or consultation page;
   - pilot or implementation page;
   - integrations or security page;
   - relevant offer-portfolio pages;
   - configured topics, workflows, and artifacts, configured secondary offers, or configured data pages.
7. Mark unsupported statements as `needs_proof` instead of strengthening them.
8. Hand off metadata to `seo-factory/04-meta-tags-builder`, FAQ expansion to `seo-factory/05-faq-builder`, JSON-LD to `seo-factory/06-schema-builder`, and link architecture/reporting to `seo-factory/07-internal-linking-builder`.
9. Save the answer-ready plan or implement scoped visible content only when the user asks for implementation.

## Outputs
- `docs/pages/<slug>/ANSWER_READY_PAGE.md` for page-level answer-ready plans.
- `docs/geo/pages/<slug>.md` for standalone GEO page plans.
- Updated scoped page/article content when implementation is explicitly requested.
- Follow-up notes for SEO, schema, FAQ, proof, and internal-link owners.

Use this output shape:

```markdown
# ANSWER_READY_PAGE: <Page / Route>

## Page
- Route:
- Topic:
- Audience:
- Funnel stage:
- AI-answer queries:

## Direct Answer
<2-4 sentence answer that can be quoted without extra context.>

## Definitions
| Term | Definition | Source/proof |
|---|---|---|

## Structured Explanation
- ...

## Comparison Table
| Option / Concept | When it fits | project position | Proof needed |
|---|---|---|---|

## Expert Block
- Expert view:
- Practical constraint:
- project recommendation:
- Proof status:

## FAQ
| Question | Short answer | Expert explanation | Schema-ready | Proof needed |
|---|---|---|---|---|

## Commercial Links
| Anchor | Target page | Reason | Funnel stage |
|---|---|---|---|

## Handoffs
- SEO metadata:
- Short definitions:
- GEO FAQ builder:
- Expert answer:
- Comparison page:
- Topic explainer:
- Schema builder:
- Internal linking:
- Proof gaps:
```

## Answer-Ready Rules
- Put the direct answer in visible page content, not only metadata or schema.
- Make definitions precise enough for an AI system to quote without changing their meaning.
- Use `geo-factory/06-topic-explainer-page-builder` for full "What is topic" pages from sitemap, SEO/GEO plans, or page queue.
- Use `geo-factory/02-short-definition-writer` for core term definitions that may be reused across pages, FAQ, glossary, and GEO briefs.
- Use structured lists for processes, criteria, use cases, limitations, and next steps.
- Use comparison tables only when the comparison is factual and useful to the buyer; use `geo-factory/05-comparison-page-builder` for full comparison pages.
- Use `geo-factory/04-expert-answer-structurer` for expert blocks that need implementation logic, limitations, safe rollout, and next step.
- Use `geo-factory/03-geo-faq-builder` for GEO FAQ blocks and keep FAQ answers direct first, then explanatory.
- Link from informational/GEO sections to commercial pages without forcing conversion language.
- Keep configured primary offer visible as the primary-offer path when the topic relates to configured domain topics, workflows, and artifacts, or configured configured analysis.

## Rules
- Do not create unsupported claims, fake citations, fake customers, ratings, prices, awards, guarantees, or invented numbers.
- Do not claim guaranteed ROI, defect reduction, audit success, certification, or implementation speed unless supported by `docs/CLAIMS_AND_PROOFS.md`.
- Do not position project as generic chatbot AI.
- Avoid visual motifs prohibited by the configured brand rules.
- Do not create doorway pages or thin pages that exist only for AI-search capture.
- Do not hide important answer content in schema only.
- Production deploy requires human approval.
