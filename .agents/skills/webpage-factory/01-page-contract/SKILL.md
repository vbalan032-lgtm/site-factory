---
name: 01-page-contract
description: Use when a queued project page needs one trusted contract before creative, copy, assets, implementation, SEO/GEO, or release work begins.
---

## Context entry

Use `shared/context-pack-loader` stdout JSON first. Read sources only via `exact_source_triggers`, changed fingerprints/conflicts, or an explicit cross-cutting audit. Never create tracked `CONTEXT_PACK.md`.

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# Page Contract

Create the single trusted `PAGE_CONTRACT.md` for one complete page. Consolidate the useful substance of the former context, business architecture, site architecture, design mapping, and page selection steps.

## Inputs

- Canonical row in `docs/site/PAGE_QUEUE.md`.
- ``exact_source_triggers` source`.
- Targeted source documents selected by `context-pack-loader`.
- Existing route, implementation, and legacy artifacts only as migration evidence.

## Workflow

1. Confirm one page, route, priority, and expected output.
2. Declare a compact `context_allowlist` before reading supporting sources.
3. Capture audience, buyer stage, offer, intent, pain, objections, claims, proof limits, CTA, route hierarchy, internal links, SEO/GEO intent, and technical constraints.
4. Calculate source fingerprints from normalized repository-relative path, raw bytes, and schema version.
5. Record decisions, unresolved items, approval scope, and minimum next-stage inputs.
6. Use final public Russian Cyrillic; retain Latin only for accepted professional terms.
7. Write `PAGE_CONTRACT.md` from `references/page-contract-template.md`.
8. Run `scripts/validate_stage.py`. Only a passing artifact may route to Stage 2 and status `contract_ready`.

## Source triggers

- Read claims sources for any metric, guarantee, customer proof, security, audit, or performance statement.
- Read sitemap/technical sources when route, rendering, integration, or release behavior is ambiguous.
- Reread a source when its recorded fingerprint changed or artifacts conflict.

## Handoff

Output only the contract and compact validation evidence. Do not create visual direction, final copy, assets, code, or block statuses. On failure, preserve canonical lifecycle state and return the smallest blocker.
