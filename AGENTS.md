# Site Factory repository rules

This repository is the brand-neutral factory product, not a customer website.

- Keep `.agents/skills` free of customer names, domains, claims, personal paths, credentials, and domain assumptions.
- Preserve Russian Cyrillic as the v1 public-language contract; brand and technical Latin terms come from `.site-factory/project.json`.
- Develop behavior test-first and run factory, bootstrap, skill, genericity, and starter gates before completion claims.
- `Attach` and `Update` may change only lock-declared factory-owned files. Never overwrite target application files or business documents.
- Read relevant local Next.js 16 documentation under `node_modules/next/dist/docs/` before changing starter framework code.
- Do not commit generated packages, `node_modules`, `.next`, test runtime directories, credentials, tokens, or user-specific Codex configuration.
- Commits, remote Git operations, releases, staging, and production require explicit human approval.

