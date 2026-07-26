# Stage context policy

The allowlists below are defaults, not permission to bulk-load every listed source. Load the smallest sufficient subset. Token budgets are soft ceilings for the context pack itself.

| Stage | Default context allowlist | Soft token budget |
|---|---|---:|
| 1 Page Contract | User request; route state; `PROJECT_MASTER_CONTEXT.md`; relevant business, product, claims, persona, sitemap, source-index, and technical sources | 8,000 |
| 2 Creative Blueprint | `PAGE_CONTRACT.md`; relevant brand/design-system rules; reference bank; route implementation as evidence | 7,000 |
| 3 Conversion Copy | `PAGE_CONTRACT.md`; approved `CREATIVE_BLUEPRINT.md`; triggered claims, SEO, GEO, persona, and product sources | 7,000 |
| 4 Assets | Validated page artifacts; existing asset/component inventory; rights and source records | 4,000 |
| 5 Full-page Build | Validated page artifacts; relevant route/components; design system; `TECH_STACK.md`; local Next.js guide | 8,000 |
| 6 Integrated QA | All current page artifacts; implemented route; applicable gate/checker rules; changed or disputed sources only | 8,000 |
| 7 Release + Growth | Canonical state; `QA_REPORT.md`; Git/CI/staging/release evidence; approved analytics or research for growth | 4,000 |

## Reload triggers

Reload an original source when its recorded fingerprint differs, a claim is disputed, two trusted artifacts conflict, an unresolved item requests it, or a specialist trigger cannot be resolved from artifacts. Record the trigger and resulting decision.

## Migration evidence

Archived page and block artifacts may explain prior intent or implementation. Label every such input `migration_evidence`; do not treat it as current approval, source-of-truth proof, or a required production pattern.
