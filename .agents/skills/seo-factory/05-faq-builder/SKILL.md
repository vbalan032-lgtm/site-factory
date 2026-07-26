---
name: 05-faq-builder
description: "Create project page FAQ blocks with 5-8 buyer-relevant questions by default, a short direct answer, expert explanation, funnel-stage alignment, proof-safe wording, and FAQPage schema readiness. Use when Codex needs FAQ content for project pages, SEO briefs, page blocks, answer-engine visibility, or schema handoff without unsupported claims."
---

## Context entry

Use `shared/context-pack-loader` stdout JSON first. Read sources only via `exact_source_triggers`, changed fingerprints/conflicts, or an explicit cross-cutting audit. Never create tracked `CONTEXT_PACK.md`.

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# 05-faq-builder

## Purpose
Create FAQ blocks for project pages that answer real buyer and search questions directly, deepen trust with expert explanation, and remain safe for visible page content and FAQPage schema.

The default page FAQ block contains 5-8 questions. If a user explicitly asks for 58 questions, create an extended FAQ set only when the page or resource format can support it; otherwise split it into a visible 5-8 question page FAQ plus a backlog of additional FAQ candidates.

## Inputs
- `docs/pages/<slug>/SEO_BRIEF.md` or `docs/seo/briefs/<slug>.md`
- `docs/seo/KEYWORD_MAP.md`
- `docs/seo/CONTENT_GAP_REPORT.md`, when the FAQ comes from a gap audit
- `docs/SITEMAP_V1.md`
- ``exact_source_triggers` source`
- ``exact_source_triggers` source`
- ``exact_source_triggers` source`
- ``exact_source_triggers` source`
- `docs/pages/<slug>/context-pack-loader stdout JSON`, when present
- Existing page copy or route content when adding FAQ to an implemented page

## Workflow
1. Identify the page route, target audience, funnel stage, search intent, and primary CTA.
2. Read the SEO brief and proof constraints. If no brief exists, load keyword map, sitemap, product, persona, and claims context.
3. Select 5-8 FAQ questions that match the page's actual job:
   - awareness: definitions, problem framing, method basics;
   - consideration: comparison, fit, implementation model, integrations, security, data requirements;
   - decision: pilot, demo, scope, proof, timeline, human control, next step;
   - retention/expansion: portfolio offers, data reuse, scaling, governance.
4. For each question, write:
   - `question`;
   - `short_answer`: one direct answer in 1-2 sentences;
   - `expert_explanation`: precise explanation with domain-specific context;
   - `funnel_stage`;
   - `proof_status`: supported, needs_proof, or avoid;
   - `schema_ready`: yes or no.
5. Remove unsupported claims, generic chatbot framing, and claims that require proof not present in `docs/CLAIMS_AND_PROOFS.md`.
6. Mark any answer that needs missing proof as `needs_proof` and keep it out of FAQPage schema until supported.
7. Save the FAQ block or hand it off to page/block/schema implementation.

## Outputs
- `docs/pages/<slug>/FAQ_BLOCK.md` for page-level FAQ content.
- `docs/seo/faq/<slug>.md` for standalone SEO FAQ planning.
- FAQ handoff notes for Stage 3 or `seo-factory/06-schema-builder`.

Use this structure:

```markdown
# FAQ_BLOCK: <route>

## Source Context
- Page:
- Funnel stage:
- Primary keyword:
- CTA:

## FAQ Items
| # | Question | Short answer | Expert explanation | Funnel stage | Proof status | Schema ready |
|---|---|---|---|---|---|---|

## Schema Handoff
- FAQPage eligible:
- Exclude from schema:
- Reason:

## Claims Review
- Supported claims:
- Needs proof:
- Removed or softened:
```

## Question Rules
- Use buyer language, not internal jargon.
- Cover objections and decision criteria, not random trivia.
- Do not duplicate page headings unless the FAQ gives a sharper answer.
- Do not create FAQ questions only to stuff keywords.
- Include questions about configured primary offer, configured topics, workflows, and artifacts, integration, security, data, human review, pilot, and portfolio offers only when relevant to the page.

## Answer Rules
- Start with a short direct answer.
- Add expert explanation that shows control, precision, traceability, and domain credibility.
- Keep answers concise enough for page UX and schema reuse.
- Do not promise guaranteed ROI, guaranteed audit pass, full engineer replacement, or universal automation.
- Do not use positioning prohibited by the configured brand rules.
- Do not invent certifications, case results, standards compliance, prices, or implementation timelines.

## FAQPage Schema Rules
- Mark `schema_ready: yes` only when the question and answer are visible on the page.
- Exclude any answer marked `needs_proof`, `avoid`, or relying on unsupported claims.
- Keep schema text consistent with visible FAQ text.
- Hand FAQPage implementation to `seo-factory/06-schema-builder`.

## Rules
- Do not implement frontend UI unless the user explicitly asks.
- Do not implement JSON-LD in this skill; prepare schema-ready content and hand off to `seo-factory/06-schema-builder`.
- Keep project framed as the positioning defined in configured business sources.
- Keep configured primary offer as primary and configured offer portfolio as scale path.
- Production deploy requires human approval.
