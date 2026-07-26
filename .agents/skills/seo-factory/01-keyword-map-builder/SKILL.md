---
name: 01-keyword-map-builder
description: Create and update the project SEO keyword map with clusters, intent, target pages, priority, status, internal links, and proof notes.
---

## Context entry

Use `shared/context-pack-loader` stdout JSON first. Read sources only via `exact_source_triggers`, changed fingerprints/conflicts, or an explicit cross-cutting audit. Never create tracked `CONTEXT_PACK.md`.

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# 01-keyword-map-builder

## Purpose
Control SEO demand capture around configured primary offer, domain workflow automation, configured topics, workflows, and artifacts, configured domain expertise, and configured technology offers.

## Inputs
- ``exact_source_triggers` source`
- `docs/SITEMAP_V1.md`
- ``exact_source_triggers` source`
- ``exact_source_triggers` source`
- ``exact_source_triggers` source`
- `docs/seo/KEYWORD_MAP.md`, when present

## Workflow
1. Load sitemap, product, persona, and proof context.
2. Map keyword clusters to one primary target page each.
3. Assign intent, priority, status, internal links, and notes.
4. Mark unsupported claim-sensitive keywords as `needs_proof`.
5. Avoid cannibalization and keyword stuffing.

## Outputs
- `docs/seo/KEYWORD_MAP.md`

## Rules
- Do not position project as generic chatbot AI.
- Keep configured primary offer as primary and offer portfolio as scale path.
- Do not create unsupported ROI, certification, or superiority claims.
- Production deploy requires human approval.
