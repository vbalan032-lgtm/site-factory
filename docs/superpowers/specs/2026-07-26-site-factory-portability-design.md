# Site Factory Portability Design

## Goal

Package the proven seven-stage website loop as a private, brand-neutral Site Factory for Russian-language Next.js 16 websites managed with Codex.

## Architecture

The factory repository is a product, not a website. Its `.agents/skills` directory is the canonical skill source. A Windows bootstrap materializes a versioned snapshot into a target project and records hashes in `.site-factory/lock.json`. Project identity, brand terms, source-of-truth paths, lifecycle paths, and knowledge-graph paths live in `.site-factory/project.json`.

The repository ships a clean Next.js starter and supports safe attachment to an existing compatible project. Attachment never overwrites application code or project-owned business documents. Updates replace only unchanged factory-owned files; local drift blocks the operation and produces a report.

## Distribution

- Private repository: `site-factory`, clean history, default branch `main`.
- First release: `v1.0.0` with ZIP, manifest, and SHA-256 checksum.
- Windows 11 and Windows PowerShell 5.1 are the supported bootstrap surface for v1.
- Internet access is allowed for exact dependency installation.
- Codex runtime, tokens, OAuth files, and secret stores are never bundled.

## Compatibility

- Next.js 16 App Router, React 19, TypeScript, Tailwind CSS 4, npm lockfile.
- Public website copy is Russian Cyrillic; configured brand and technical terms may use Latin characters.
- The lifecycle, artifacts, approvals, source fingerprints, Graphify fallback, and release safety gates remain compatible with Factory v3.

## Safety

- No first-project names, domain names, claims, personal paths, credentials, or migration archives in the generic repository.
- `Attach`, `Update`, and `ConfigureCodex` are dry-run operations until `-Apply` is present.
- Production deployment is outside the factory release workflow and always requires separate human approval.
- The first project is migrated only after the generic `v1.0.0` release passes all gates.

## Acceptance

The release must create a clean starter, attach without changing sentinel application files, update an unchanged snapshot, reject drift, run with an isolated Codex profile, pass factory tests and Next quality gates, and reinstall from its own ZIP with matching checksums.

