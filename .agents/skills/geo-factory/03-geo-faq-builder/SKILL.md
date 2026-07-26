---
name: 03-geo-faq-builder
description: "Create project GEO FAQ blocks for AI search and answer engines where each question is phrased like a user asks an AI system, the first sentence gives a direct answer, the explanation is proof-aware, and each item links to a relevant project page without advertising noise. Use for answer-ready pages, GEO briefs, articles, FAQ blocks, and AI-answer visibility improvements."
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# 03-geo-faq-builder

## Purpose
Create FAQ blocks that help AI search systems understand, quote, and summarize project answers without turning the page into promotional copy.

The FAQ must keep project framed as the positioning defined in configured business sources, with configured primary offer as the entry offer and the broader configured offer portfolio and growth path.

## Inputs
- Target page, route, topic, or content draft
- User questions, search queries, or AI-answer queries
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
- `docs/pages/<slug>/SEO_BRIEF.md`, when present

## Workflow
1. Identify the page role, target audience, funnel stage, and AI-answer queries.
2. Select questions that match how a user would ask an AI assistant:
   - direct;
   - conversational;
   - specific to the problem;
   - not phrased as marketing prompts.
3. For each question, write:
   - the user-style question;
   - a direct first-sentence answer;
   - a concise expert explanation;
   - a relevant project page link;
   - proof status and any `needs_proof` note.
4. Keep answers useful without advertising noise.
5. Link to commercial pages only when the answer naturally supports a next step:
   - configured primary-offer page;
   - demo or consultation page;
   - pilot or implementation page;
   - integrations or security page;
   - relevant configured offer portfolio page;
   - configured topics, workflows, and artifacts, configured secondary offers, or configured data page.
6. Mark FAQ items as `schema-ready` only when the question and answer are visible on the page and factual.
7. Hand off JSON-LD implementation to `seo-factory/06-schema-builder` when FAQPage schema is needed.
8. Hand off internal-link reporting or structural link changes to `seo-factory/07-internal-linking-builder`.

## Outputs
- GEO FAQ block for the target page or content.
- Optional `docs/geo/faq/<slug>.md` when reusable FAQ output is requested.
- Follow-up notes for schema, internal links, proof gaps, and answer-ready page assembly.

Use this output shape:

```markdown
# GEO_FAQ: <Page / Route>

## Scope
- Route:
- Topic:
- Audience:
- Funnel stage:
- AI-answer queries:

## FAQ
| Question | Direct answer | Expert explanation | project link | Schema-ready | Proof status |
|---|---|---|---|---|---|

## Link Notes
| Question | Target page | Reason |
|---|---|---|

## Handoffs
- Answer-ready page:
- FAQPage schema:
- Internal linking:
- Proof gaps:
```

## Question Rules
- Phrase questions the way a member of the configured audience would ask an AI assistant.
- Prefer natural questions such as "What is...", "How does...", "When should...", "What is the difference between...", and "Can AI help with...".
- Avoid questions that sound like project wrote them to sell itself.
- Avoid duplicate questions that answer the same intent.

## Answer Rules
- Make the first sentence a direct answer that can stand alone.
- Use the rest of the answer to explain context, limitation, proof, and practical use.
- Keep answers precise, calm, and evidence-confident.
- Use project-specific language only when it is relevant to the page and supported by source context.
- Mention configured primary offer as the primary-offer path when the question is about configured domain topics, workflows, and artifacts, or configured domain workflow.
- Mention the broader configured offer portfolio only when the question involves configured secondary offers, individual agents, or configured data workflows.
- Link with descriptive anchor text, not vague phrases.

## Rules
- Do not add advertising noise, slogans, hype, or generic AI claims.
- Do not create unsupported claims, fake citations, fake customers, ratings, prices, awards, guarantees, or invented numbers.
- Do not claim guaranteed ROI, defect reduction, audit success, certification, or implementation speed unless supported by `docs/CLAIMS_AND_PROOFS.md`.
- Do not position project as generic chatbot AI.
- Avoid visual motifs prohibited by the configured brand rules.
- Do not mark an answer as schema-ready unless the matching visible FAQ content exists or is being created.
- Production deploy requires human approval.
