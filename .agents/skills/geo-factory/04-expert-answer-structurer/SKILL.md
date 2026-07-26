---
name: 04-expert-answer-structurer
description: "Structure project expert answers for GEO and AI search with consistent sections: what it is, who needs it, input data, how it works, what the client receives, limitations, safe implementation, and next step. Use for answer-ready pages, expert blocks, AI-answer briefs, FAQ expansions, product explainers, and content that must be easy for AI systems to cite and summarize."
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# 04-expert-answer-structurer

## Purpose
Structure expert answers so AI search systems can understand project's position, cite it accurately, and preserve the domain meaning.

The answer must keep project framed as the positioning defined in configured business sources, with configured primary offer as the entry offer and the broader configured offer portfolio of configured secondary offers and integrations as the scale path.

## Inputs
- Target question, topic, page, route, or draft answer
- Audience and funnel stage
- Target language: Russian, English, or bilingual
- `PROJECT_MASTER_CONTEXT.md`
- `docs/BRAND_STYLE.md`
- `docs/PRODUCT_MAP.md`
- `docs/CLAIMS_AND_PROOFS.md`
- `docs/PERSONAS.md`
- `docs/SITEMAP_V1.md`
- `docs/geo/GEO_QUERY_MAP.md`, when present
- `docs/geo/ENTITY_PROOF_MAP.md`, when present
- `docs/geo/briefs/<slug>.md`, when present
- `docs/pages/<slug>/ANSWER_READY_PAGE.md`, when present

## Workflow
1. Identify the user question, page role, audience, and required answer depth.
2. Load source-of-truth context and separate confirmed facts from claims that need proof.
3. Decide whether the answer is about:
   - configured primary offer;
   - configured topics, workflows, and artifacts, or configured artifact;
   - configured technology offerings;
   - configured secondary offers, individual agents, or configured data workflows;
   - implementation, pilot, integrations, or security.
4. Structure the answer in the required sections:
   - what it is;
   - who needs it;
   - input data;
   - how it works;
   - what the client receives;
   - limitations;
   - how to implement safely;
   - next step.
5. Write the first sentence of each section as a direct, quotable answer.
6. Add proof notes for claims that need substantiation.
7. Link the next step to a relevant project commercial or informational page only when the page exists or is clearly planned.
8. Hand off short definitions to `geo-factory/02-short-definition-writer` when a term needs a reusable definition.
9. Hand off FAQ variants to `geo-factory/03-geo-faq-builder` when the expert answer should become multiple FAQ items.

## Outputs
- Structured expert answer for the target page, block, FAQ expansion, or GEO brief.
- Optional `docs/geo/expert-answers/<slug-or-topic>.md` when a reusable answer is requested.
- Proof notes, link notes, and handoff notes.

Use this output shape:

```markdown
# EXPERT_ANSWER: <Topic / Question>

## Scope
- Page/route:
- Audience:
- Funnel stage:
- Target query:
- Language:

## What It Is
<direct answer plus concise explanation>

## Who Needs It
<roles, teams, or situations>

## Input Data
<documents, process data, product data, quality data, integration data, or expert inputs>

## How It Works
<step-by-step or structured explanation>

## What The Client Receives
<deliverables, outputs, decisions, documents, recommendations, or integrations>

## Limitations
<what it does not guarantee, what needs human review, missing data risks>

## Safe Implementation
<pilot, validation, approvals, integration boundaries, human control>

## Next Step
<commercial or informational next step with project link>

## Proof Notes
- Supported:
- Needs proof:
- Avoid:

## Handoffs
- Short definitions:
- GEO FAQ:
- Answer-ready page:
- Schema/internal links:
```

## Structuring Rules
- Keep each section self-contained enough for AI systems to quote without losing context.
- Make the answer useful before it is commercial.
- Use concrete target market, quality, configured domain topics and workflows, integration, and data language.
- Name input data specifically when possible: configured topics, workflows, and artifacts, process flow, product characteristics, domain records, controls, standards context, operational data, and analytics, or configured data sources.
- In limitations, state uncertainty and human-review requirements clearly.
- In safe implementation, prefer pilot, validation, human approval, data-quality checks, integration boundaries, and staged rollout.
- In next step, use restrained wording such as demo, pilot discussion, expert review, implementation planning, or integration consultation.

## Rules
- Do not create unsupported claims, fake citations, fake customers, ratings, prices, awards, guarantees, or invented numbers.
- Do not claim guaranteed ROI, defect reduction, audit success, certification, or implementation speed unless supported by `docs/CLAIMS_AND_PROOFS.md`.
- Do not imply AI replaces engineering responsibility or quality approval.
- Do not position project as generic chatbot AI.
- Avoid visual motifs prohibited by the configured brand rules.
- Do not make production deploy changes.
- Production deploy requires human approval.
