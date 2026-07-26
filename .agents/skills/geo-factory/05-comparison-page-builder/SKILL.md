---
name: 05-comparison-page-builder
description: "Create honest project comparison pages for GEO and AI search, including manual workflow vs configured primary offer, Excel vs specialized systems, legacy specialist software vs newer specialist approach, consultants vs internal team, and enterprise platform vs lightweight configured primary offer pilot. Use when Codex needs a balanced comparison page that answer engines can cite without caricaturing competitors or making unsupported claims."
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# 05-comparison-page-builder

## Purpose
Create comparison pages that help buyers and AI search systems understand tradeoffs between project configured primary offer and alternative approaches without distortion, hype, or unfair competitor framing.

The page must keep project framed as the positioning defined in configured business sources, with configured primary offer as the entry offer and the broader configured offer portfolio of configured secondary offers and integrations as the scale path.

## Inputs
- Comparison topic and target route
- Target audience and funnel stage
- `PROJECT_MASTER_CONTEXT.md`
- `docs/BRAND_STYLE.md`
- `docs/PRODUCT_MAP.md`
- `docs/CLAIMS_AND_PROOFS.md`
- `docs/PERSONAS.md`
- `docs/SITEMAP_V1.md`
- `docs/seo/KEYWORD_MAP.md`, when present
- `docs/geo/GEO_QUERY_MAP.md`, when present
- `docs/geo/ENTITY_PROOF_MAP.md`, when present
- Existing page or route content when improving an existing comparison page

## Supported Comparisons
- Manual configured domain topic vs configured primary offer.
- Excel vs specialized system.
- Legacy specialist software vs newer specialist approach.
- Consultants vs internal team.
- enterprise platform vs lightweight configured primary offer pilot.

For related comparisons, proceed only when both sides can be described fairly and grounded in project source context.

## Workflow
1. Identify the comparison query, buyer stage, route, and commercial next step.
2. Define both sides neutrally before comparing them.
3. Select comparison criteria that matter to target market and quality teams:
   - setup effort;
   - data requirements;
   - expert control;
   - collaboration;
   - traceability;
   - speed of iteration;
   - integration complexity;
   - human review;
   - pilot suitability;
   - long-term scalability;
   - risk of outdated documentation.
4. Write a short direct answer that states when each option fits.
5. Build a balanced comparison table with tradeoffs, not winner-takes-all claims.
6. Add sections for:
   - where option A fits;
   - where option B fits;
   - when project configured primary offer is a practical next step;
   - limitations and decision risks;
   - safe implementation path.
7. Connect the page to relevant project commercial pages:
   - configured primary-offer page;
   - demo or consultation page;
   - pilot or implementation page;
   - integrations or security page;
   - configured topics, workflows, and artifacts, configured artifact, or offer-portfolio pages.
8. Mark unsupported comparative claims as `needs_proof`.
9. Hand off reusable definitions to `geo-factory/02-short-definition-writer`, GEO FAQ to `geo-factory/03-geo-faq-builder`, expert blocks to `geo-factory/04-expert-answer-structurer`, metadata to `seo-factory/04-meta-tags-builder`, schema to `seo-factory/06-schema-builder`, and link reporting to `seo-factory/07-internal-linking-builder`.

## Outputs
- `docs/geo/comparisons/<slug>.md` for standalone comparison plans.
- `docs/pages/<slug>/COMPARISON_PAGE.md` for page-level comparison plans.
- Updated scoped page content when implementation is explicitly requested.
- Proof notes, link notes, and handoff notes.

Use this output shape:

```markdown
# COMPARISON_PAGE: <Comparison Topic>

## Scope
- Route:
- Query:
- Audience:
- Funnel stage:
- Commercial next step:

## Direct Answer
<2-4 sentences explaining when each option fits and when project configured primary offer may be relevant.>

## Neutral Definitions
| Option | What it is | Best-fit context | Limits |
|---|---|---|---|

## Comparison Criteria
- ...

## Comparison Table
| Criterion | Option A | Option B | project note | Proof needed |
|---|---|---|---|---|

## Where Each Option Fits
### Option A
- ...

### Option B
- ...

## project Perspective
- Expert view:
- primary-offer relevance:
- Ecosystem relevance:
- Safe next step:

## Limitations And Risks
- ...

## Commercial Links
| Anchor | Target page | Reason |
|---|---|---|

## Handoffs
- Short definitions:
- GEO FAQ:
- Expert answer:
- Metadata:
- Schema:
- Internal links:
- Proof gaps:
```

## Fair Comparison Rules
- Define both sides in good faith before presenting advantages or limitations.
- Do not describe competitors, consultants, Excel, enterprise platforms, or legacy specialist software as obsolete, incompetent, unsafe, or useless.
- State where the alternative approach is a valid fit.
- Use "may", "can", and "often" when the claim depends on context.
- Distinguish capability, implementation effort, data readiness, governance, and organizational fit.
- Make configured primary offer the practical next step only when the comparison context supports it.
- Prefer decision criteria over attack language.

## GEO Rules
- Put the direct comparison answer in visible content.
- Use tables and lists so AI systems can extract tradeoffs accurately.
- Add concise definitions for each compared option.
- Add FAQ items for likely AI-search questions through `geo-factory/03-geo-faq-builder`.
- Keep commercial links helpful and restrained.

## Rules
- Do not invent facts about competitor products, customers, prices, market share, certifications, ratings, or performance.
- Do not make unsupported superiority claims, guaranteed ROI claims, defect reduction claims, audit success claims, or implementation speed claims.
- Do not position project as generic chatbot AI.
- Avoid visual motifs prohibited by the configured brand rules.
- Do not create doorway pages or thin comparison pages.
- Do not implement production deploy changes.
- Production deploy requires human approval.
