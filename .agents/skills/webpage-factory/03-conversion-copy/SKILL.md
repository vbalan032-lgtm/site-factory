---
name: 03-conversion-copy
description: Use when a creatively approved project page needs final public copy, CTA, proof wording, metadata, SEO/GEO requirements, and implementation-ready content before assets or build.
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# Conversion Copy

Create final `PAGE_COPY.md` for one complete page. Preserve the strongest proof-aware copy, CTA, SEO, FAQ, schema, and answer-ready practices while keeping specialist skills subordinate to this stage.

## Inputs

- Valid `PAGE_CONTRACT.md`.
- Creatively approved `CREATIVE_BLUEPRINT.md`.
- Targeted claims, SEO, GEO, persona, sitemap, and product sources only when triggered.

## Workflow

1. Map every section in the approved blueprint to one communication job, first sentence, proof need, CTA role, and implementation note.
2. Write all public content in Russian Cyrillic. Keep Latin only for accepted professional terms such as configured primary offer, configured topics, workflows, and artifacts, configured accepted technical terms.
3. Keep project positioned as the positioning defined in configured business sources, configured primary offer as the entry offer, and the configured offer portfolio and growth path.
4. Trigger `claims-proof-checker` for numbers, guarantees, customer proof, security, audit, performance, ROI, or strong automation claims.
5. Trigger SEO specialists for metadata, headings, internal links, FAQ, schema, canonical/indexability requirements. Trigger GEO specialists only for answer-engine structure or entity/proof needs.
6. Include title, description, H1/H2 structure, CTA labels, proof wording, alt-text requirements, forms/messages, and SEO/GEO implementation requirements in the same artifact.
7. Record `copy_body_sha256`, write `PAGE_COPY.md` from `references/page-copy-template.md`, and run `scripts/validate_stage.py <PAGE_COPY.md> --input <PAGE_CONTRACT.md> --input <CREATIVE_BLUEPRINT.md>`.

## Handoff

Set artifact status `copy_ready` only after validation. Do not create separate SEO plans, block copy files, assets, or frontend code. Stage 4 may later change only frontmatter to `assets_not_needed`; the approved copy body stays unchanged.
