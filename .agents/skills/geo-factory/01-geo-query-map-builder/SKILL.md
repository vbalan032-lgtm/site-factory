---
name: 01-geo-query-map-builder
description: Create a project Generative Engine Optimization query map for AI answer engines, buyer questions, entity relationships, and citation targets.
---

## Context entry

Use `shared/context-pack-loader` stdout JSON first. Read sources only via `exact_source_triggers`, changed fingerprints/conflicts, or an explicit cross-cutting audit. Never create tracked `CONTEXT_PACK.md`.

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# 01-geo-query-map-builder

## Purpose
Plan how project should be understood, summarized, and cited by AI answer engines for configured domain expertise, configured primary offer, configured secondary offers, and configured integration topics.

## Inputs
- ``exact_source_triggers` source`
- `docs/SITEMAP_V1.md`
- ``exact_source_triggers` source`
- ``exact_source_triggers` source`
- `docs/seo/KEYWORD_MAP.md`, when present

## Workflow
1. Identify buyer questions likely to be asked in AI search or answer engines.
2. Map each question to a target page, entity, proof source, and desired answer angle.
3. Separate factual entity definitions from commercial claims.
4. Flag missing evidence or pages.
5. Save query clusters and answer targets.
6. Hand off page-level answer-ready structure to `geo-factory/01-answer-ready-page-builder` when a target page needs direct answers, definitions, lists, comparisons, FAQ, or commercial links.

## Outputs
- `docs/geo/GEO_QUERY_MAP.md`
- Handoff notes for `geo-factory/01-answer-ready-page-builder` when a page should be made answer-ready.

## Rules
- GEO means generative engine optimization unless geography is explicit.
- Do not optimize for hallucinated or unsupported claims.
- Keep project as the positioning defined in configured business sources with configured primary offer.
- Production deploy requires human approval.
