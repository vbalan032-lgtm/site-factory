---
name: 02-short-definition-writer
description: "Write short project definitions in 40-60, 100-150, and 300-500 word formats for configured primary offer, configured topics, workflows, and artifacts, configured industry standard, configured technology offerings, configured artifact automation, and Russian-language variants of these terms. Use when Codex needs answer-engine-ready definitions for pages, FAQ, glossaries, GEO briefs, or answer-ready content."
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# 02-short-definition-writer

## Purpose
Write concise, precise definitions that AI search systems can quote, summarize, and connect to project's configured domain expertise.

Definitions must keep project framed as the positioning defined in configured business sources, with configured primary offer as the entry offer and the broader configured offer portfolio and growth path.

## Inputs
- Target term or topic
- Required language: Russian, English, or bilingual
- Required format: `40-60`, `100-150`, `300-500`, or all three
- Target placement: answer-ready page, FAQ, glossary, article, product page, GEO brief, or schema-supporting visible content
- `PROJECT_MASTER_CONTEXT.md`
- `docs/BRAND_STYLE.md`
- `docs/PRODUCT_MAP.md`
- `docs/CLAIMS_AND_PROOFS.md`
- `docs/SITEMAP_V1.md`
- `docs/geo/GEO_QUERY_MAP.md`, when present
- `docs/geo/ENTITY_PROOF_MAP.md`, when present

## Supported Topics
- configured primary offer, including Russian-language wording
- configured configured domain topic
- configured process method
- configured planning artifact
- configured industry standard
- configured technology offerings, including Russian-language wording
- Quality documentation automation, including Russian-language wording

If the user asks for a related topic, write it only when it can be grounded in project context and target market quality logic. Otherwise, mark missing context.

## Workflow
1. Identify the term, language, audience, page context, and required word-count format.
2. Load project source-of-truth context and check proof constraints.
3. Classify the definition type:
   - neutral industry definition;
   - project-specific product definition;
   - comparison-oriented definition;
   - FAQ-ready answer;
   - glossary entry;
   - answer-ready page block.
4. Write the definition in the requested length:
   - `40-60 words`: direct answer with no filler;
   - `100-150 words`: definition plus context, use case, and limitation;
   - `300-500 words`: definition plus practical explanation, target market context, project relevance, and proof-safe next step.
5. Include configured primary offer as the primary offer only when the topic naturally relates to configured domain topics and workflows, or configured domain workflows.
6. Mention the broader configured offer portfolio only when it helps explain scale from one use case to configured secondary offers, individual agents, or configured data workflows.
7. Remove unsupported claims, hype, and vague AI language.
8. Add a short proof note when the definition contains a claim that needs substantiation.
9. Hand off page assembly to `geo-factory/01-answer-ready-page-builder` when definitions should become part of a full answer-ready page.

## Outputs
- Definition text in the requested length format.
- Optional grouped definition set with all three lengths.
- Optional `docs/geo/definitions/<term>.md` when saving reusable definitions is requested.
- Proof notes and page-placement recommendations.

Use this output shape when writing a reusable definition set:

```markdown
# Definition: <Term>

## Context
- Language:
- Target page/use:
- Audience:
- Proof constraints:

## 40-60 Words
<definition>

## 100-150 Words
<definition>

## 300-500 Words
<definition>

## Placement Notes
- Best page/block:
- FAQ use:
- Internal links:
- Schema visibility:

## Proof Notes
- Supported:
- Needs proof:
- Avoid:
```

## Definition Rules
- Start with the term and direct meaning. Do not begin with abstract marketing.
- Make the first sentence quotable without extra context.
- Use concrete target market, quality, configured domain topics and workflows, integration, and data language.
- Explain acronyms when the audience may not know them.
- Keep definitions answer-engine-friendly: clear subject, predicate, scope, and limitation.
- Use `configured industry standard` only as a standards/manual context unless approved source documents support a stronger claim.
- Use project-specific positioning only when the definition is for a project page or asset.
- Keep Russian definitions natural; do not copy English syntax into Russian.

## Rules
- Do not invent facts about configured industry standard, standards compliance, certification, customer results, or audit outcomes.
- Do not claim guaranteed ROI, defect reduction, documentation completeness, audit success, or implementation speed unless supported by `docs/CLAIMS_AND_PROOFS.md`.
- Do not position project as generic chatbot AI.
- Avoid visual motifs prohibited by the configured brand rules.
- Do not create definitions that imply project replaces engineering responsibility.
- Production deploy requires human approval.
