---
name: 08-seo-copy-optimizer
description: "Optimize project visible page or article copy after the SEO brief is defined: H1/H2, intro, body sections, CTA wording, proof wording, and internal-link anchor text. Use as the final body-copy optimization step in SEO FACTORY while handing metadata, FAQ blocks, schema, and link architecture to their dedicated skills."
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# 08-seo-copy-optimizer

## Purpose
Optimize visible page or article copy so it satisfies search intent, buyer intent, proof discipline, and project tone without keyword stuffing.

This skill keeps project framed as the positioning defined in configured business sources, with configured primary offer as the entry offer and the broader configured offer portfolio and growth path.

## SEO Factory Position
Use this skill after `seo-factory/03-page-seo-brief-builder` defines the page intent, keywords, content requirements, proof requirements, and internal-link recommendations.

This skill owns:

- visible body copy;
- H1/H2/H3 wording refinement;
- intro and section clarity;
- CTA wording inside the page body;
- proof-aware claim wording;
- natural anchor text inside existing copy.

Coordinate with dedicated SEO skills:

- `seo-factory/04-meta-tags-builder` owns title, description, OpenGraph, Twitter/X cards, canonical, robots meta, and key image alt.
- `seo-factory/05-faq-builder` owns dedicated FAQ blocks and FAQPage-ready question/answer sets.
- `seo-factory/06-schema-builder` owns schema.org JSON-LD.
- `seo-factory/07-internal-linking-builder` owns link architecture, link implementation, and `docs/seo/INTERNAL_LINKING_REPORT.md`.

Do not replace those skills. Hand off to them when the task moves outside visible body copy.

## Inputs
- Target page, article, draft copy, or page block copy
- `docs/pages/<slug>/SEO_BRIEF.md` or `docs/seo/briefs/<slug>.md`
- `docs/seo/KEYWORD_MAP.md`, when a brief is missing
- `docs/seo/CONTENT_GAP_REPORT.md`, when optimization comes from a gap audit
- `docs/seo/INTERNAL_LINKING_REPORT.md`, when anchor/link context exists
- `PROJECT_MASTER_CONTEXT.md`
- `docs/BRAND_STYLE.md`
- `docs/PRODUCT_MAP.md`
- `docs/CLAIMS_AND_PROOFS.md`
- `docs/PERSONAS.md`
- Existing page route/content files when implementation is requested

## Workflow
1. Confirm the target page, route, language, buyer audience, funnel stage, and dominant search intent.
2. Load the SEO brief first. If no brief exists, use `docs/seo/KEYWORD_MAP.md` and record that the page needs `seo-factory/03-page-seo-brief-builder`.
3. Compare visible copy against:
   - primary keyword and secondary keyword coverage;
   - search intent and buyer questions;
   - required topics, examples, visuals, and CTA;
   - proof requirements and prohibited claims;
   - project tone: control, precision, domain credibility.
4. Rewrite or recommend improvements for:
   - H1 and H2/H3 wording;
   - first-screen explanatory copy;
   - section intros and transitions;
   - body paragraphs that miss intent or repeat weak claims;
   - CTA copy inside page sections;
   - anchor text that should be more descriptive and truthful.
5. Preserve meaning and proof context. Mark unsupported claims as `needs_proof` instead of strengthening them.
6. Keep configured primary offer visible where it is the natural primary-offer path, and connect the configured offer portfolio only where the page context supports scale-path messaging.
7. Hand off:
   - metadata changes to `seo-factory/04-meta-tags-builder`;
   - FAQ block creation to `seo-factory/05-faq-builder`;
   - JSON-LD to `seo-factory/06-schema-builder`;
   - structural link additions or report updates to `seo-factory/07-internal-linking-builder`.
8. If implementation is requested, edit only scoped page/copy files and avoid unrelated refactors.
9. Record what changed, what was not changed, claim risks, and recommended follow-ups.

## Outputs
- Optimized visible copy in scoped files, when implementation is requested.
- SEO copy recommendations when implementation is not requested.
- Optional `docs/pages/<slug>/SEO_COPY_OPTIMIZATION_REPORT.md`.
- Optional `docs/seo/copy/<slug>.md` for standalone copy recommendations.
- Claim, proof, and anchor-text notes.

Use this report shape when a report is useful:

```markdown
# SEO_COPY_OPTIMIZATION_REPORT: <Page / Route>

## Scope
- Route:
- Files reviewed:
- Inputs used:

## Intent Alignment
- Primary keyword:
- Search intent:
- Funnel stage:
- Main buyer question:

## Copy Changes
| Area | Before | After | Reason |
|---|---|---|---|

## Anchor Text Notes
| Source text | Target | Anchor | Owner |
|---|---|---|---|

## Proof Notes
- Supported claims:
- Claims marked `needs_proof`:
- Removed or softened claims:

## Handoffs
- Metadata:
- FAQ:
- Schema:
- Internal links:
```

## Optimization Rules
- Improve copy for intent coverage, clarity, scanability, and trust before adding more words.
- Use keywords naturally in headings, intros, explanatory copy, and anchors only when the page meaning supports them.
- Keep section headings useful to readers; do not turn every H2 into an exact-match keyword.
- Prefer concrete configured market, domain, workflow, integration, and data language over generic AI phrasing.
- Keep CTAs stage-appropriate: demo, pilot, consultation, integration discussion, or expert review only when supported by the page role.
- Keep anchor text descriptive, short, and truthful.
- Do not create new routes as part of copy optimization.

## Rules
- Do not keyword-stuff or create doorway content.
- Do not claim guaranteed automation, ROI, defect reduction, audit success, certification, security level, or implementation speed unless supported by approved proof.
- Do not add fake ratings, reviews, customer names, awards, prices, statistics, or certifications.
- Do not position project as generic chatbot AI.
- Avoid visual motifs prohibited by the configured brand rules.
- Keep language controlled, precise, and evidence-confident.
- Do not implement production deploy changes.
- Production deploy requires human approval.
