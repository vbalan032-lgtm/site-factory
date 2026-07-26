---
name: brand-compliance-checker
description: "Use when a project page artifact, SEO/GEO output, or release candidate needs a scoped brand-compliance review."
---

## Context entry

Use `shared/context-pack-loader` stdout JSON first. Read sources only via `exact_source_triggers`, changed fingerprints/conflicts, or an explicit cross-cutting audit. Never create tracked `CONTEXT_PACK.md`.

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# brand-compliance-checker

## Purpose
Check whether a specific artifact follows project brand positioning and communication rules. This skill only checks; it does not write positioning, create a brand book, or edit the whole site.

## Inputs
- Artifact to check: copy, page, block, visual brief, SEO/GEO page, CTA, FAQ, metadata, or QA artifact.
- ``exact_source_triggers` source`.
- ``exact_source_triggers` source`.
- ``exact_source_triggers` source`, when product or offer portfolio meaning matters.
- ``exact_source_triggers` source`, when audience or CTA fit matters.
- ``exact_source_triggers` source`, when claims appear.

## Workflow
1. Identify the artifact type, audience, funnel stage, and public surface.
2. Check whether the artifact keeps project positioned as the positioning defined in configured business sources.
3. Check whether configured primary offer is treated as the primary offer where relevant.
4. Check whether the configured offer portfolio is presented as the scale path without confusing the offer.
5. Flag brand drift, generic chatbot framing, hype, weak tone, or prohibited imagery/wording.
6. Provide findings with severity and minimal fix direction.

## Outputs
- Brand compliance check report.
- Pass/fail status, blockers, warnings, and owner skill routing.

Use this report shape:

```markdown
# BRAND_COMPLIANCE_REPORT

## Scope
- Artifact:
- Audience:
- Sources used:

## Status
- Result: pass / pass_with_warnings / fail
- Release blocker:

## Findings
| Severity | Area | Finding | Evidence | Owner skill |
|---|---|---|---|---|

## Required Fixes
- ...
```

## Used Inside
- Stage 2 for visual-direction findings.
- Stage 3 for public-copy/SEO/GEO findings.
- Stage 6 for integrated brand review and release-blocking findings.

Return findings to the owning stage; do not edit its artifact or become a parallel owner.

## Rules
- Do not write positioning; route that to `website-factory/06-positioning-builder`.
- Do not create or edit the brand book.
- Do not edit the whole site.
- Do not approve framing prohibited by the configured brand rules.
- Do not approve unsupported claims; route claim risk to `shared/claims-proof-checker`.
- Production deploy requires human approval.
