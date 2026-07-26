---
name: claims-proof-checker
description: "Use when a project contract, public copy, SEO/GEO artifact, or release candidate contains claims, numbers, comparisons, guarantees, or proof risk."
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# claims-proof-checker

## Purpose
Check claims in one concrete artifact against approved proof constraints. This skill only reviews claims; it does not write `CLAIMS_AND_PROOFS.md` and does not invent evidence.

## Inputs
- Text, page, block, FAQ, metadata, schema copy, GEO content, comparison page, or QA candidate.
- `docs/CLAIMS_AND_PROOFS.md`.
- `PROJECT_MASTER_CONTEXT.md`.
- `docs/PRODUCT_MAP.md`, when product claims appear.
- Source materials named by the user, when available.

## Workflow
1. Extract factual, numeric, comparative, certification, security, ROI, performance, automation, and outcome claims.
2. Match each claim to approved proof level or mark `needs_proof`.
3. Flag prohibited promises and risky absolutes.
4. Identify claims that imply AI fully replaces engineers or quality responsibility.
5. Suggest safe wording only for the specific claim.
6. Return findings before any summary.

## Outputs
- Claims proof check report.
- Claim-by-claim status.
- Safe wording suggestions and proof gaps.

Use this report shape:

```markdown
# CLAIMS_PROOF_CHECK_REPORT

## Scope
- Artifact:
- Sources used:

## Status
- Result: pass / pass_with_warnings / fail
- Release blocker:

## Findings
| Severity | Claim | Status | Evidence/proof note | Suggested wording |
|---|---|---|---|---|

## Proof Gaps
- ...
```

## Used Inside
- Stage 1 for contract claim/proof limits.
- Stage 3 for copy, SEO, GEO, metadata, FAQ, and schema claims.
- Stage 6 for integrated release-candidate verification.

Return findings to the owning stage; never approve or mutate its lifecycle state.

## Rules
- Do not write or update `docs/CLAIMS_AND_PROOFS.md`.
- Do not invent proof, customers, numbers, awards, certifications, ratings, prices, or benchmarks.
- Do not approve guaranteed ROI, guaranteed defect reduction, guaranteed audit success, full automation, or full engineer replacement without approved proof.
- Keep strong claims adjacent to proof context.
- Production deploy requires human approval.
