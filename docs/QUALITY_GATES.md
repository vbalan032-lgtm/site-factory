# Quality and Safety Gates

Каждый результат должен содержать sources, assumptions/gaps, changed files, checks, approvals и next safe action.

## Content and proof

- public text is Russian unless the project config allows a Latin technical term;
- unsupported facts are `needs_proof`, not public assertions;
- no guaranteed ROI, guaranteed audit success, total replacement of engineers or invented numbers;
- claims/proofs and brand review run before a copy package is review-ready.

## UI and page QA

- full-page desktop and mobile render;
- layout variety and responsive collapse;
- keyboard navigation and accessibility;
- overflow, links, forms, metadata, canonical, OpenGraph and schema;
- SSR/indexability, lint, typecheck, tests and build;
- Playwright/browser evidence only when configured or explicitly triggered.

## Assets

Every asset is classified as `reuse`, `adaptation`, `code-native`, `raster generation` or `omission`. New assets require an approved blueprint goal, source/rights, format, placement, responsive dimensions, payload risk and Russian alt text.

## Release

QA approval, staging evidence, rollback readiness and explicit page-specific production approval are separate gates. No production release is implied by build, QA or staging preparation.
