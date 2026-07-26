---
name: visual-compliance-checker
description: "Use when a project Creative Blueprint, visual asset, design-system change, or implemented page needs scoped visual-compliance findings."
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# visual-compliance-checker

## Purpose
Check whether a visual artifact follows project's visual system and configured market style. This skill only checks; it does not create the design system and does not generate illustrations.

## Inputs
- Visual brief, page/block package, UI screenshot, component, heavy illustration report, or implemented UI.
- `docs/BRAND_STYLE.md`.
- `docs/DESIGN_SYSTEM.md`, when present.
- `PROJECT_MASTER_CONTEXT.md`, when visual meaning depends on positioning.
- Relevant page/block brief when present.

## Workflow
1. Identify the visual artifact and intended page/block context.
2. Check layout, hierarchy, density, spacing, typography, color, radii, icons, illustrations, data visuals, and CTA treatment.
3. Verify that visuals communicate control, precision, traceability, domain credibility, documents, process, proof, or domain data.
4. Flag visual drift, generic AI styling, decorative noise, unsupported imagery, weak accessibility, overlap, or text-fit risks.
5. Return blockers, warnings, and owner skill routing.

## Outputs
- Visual compliance report.
- Pass/fail status, blockers, warnings, and fix owners.

Use this report shape:

```markdown
# VISUAL_COMPLIANCE_REPORT

## Scope
- Artifact:
- Files/screens reviewed:
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
- Stage 2 for Creative Blueprint findings.
- Stage 4 for approved asset findings.
- Stage 6 for implemented full-page findings.
- `website-factory/04-design-system-builder` for foundation validation.

Return findings to the owning stage. Legacy Webblock material may be reviewed only as migration evidence/focused repair.

## Rules
- Do not create the design system; route creation to `website-factory/04-design-system-builder`.
- Do not generate illustrations; route approved conditional static art to Stage 4 `canvas-design`, and code-native visuals to the owning page stage.
- Do not implement frontend code.
- Do not approve visual motifs prohibited by the configured brand rules.
- Production deploy requires human approval.
