# Site Factory Portability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. Use superpowers:test-driven-development for every behavior change and superpowers:verification-before-completion before completion claims.

**Goal:** Build and release a brand-neutral, Windows-portable Site Factory for Russian Next.js 16 websites and then connect the first project as a consumer.

**Architecture:** Store generic skills and runtime code in a clean repository. Configure each target through `.site-factory/project.json`, install a hashed snapshot into `.agents/skills`, and operate it through one PowerShell bootstrap. Keep website content and credentials project-owned.

**Tech Stack:** Python 3.12 standard library, Windows PowerShell 5.1, Next.js 16.2.12, React 19.2.4, TypeScript, Tailwind CSS 4, Graphify 0.9.13, GitHub Actions.

## Global Constraints

- Public copy is Russian Cyrillic in v1.
- The generic repository contains no first-project identity, claims, domain, personal paths, or secrets.
- Existing target application files and business documents are never overwritten by Attach or Update.
- Remote Git, meaningful commits, releases, and production actions require explicit human approval.

---

### Task 1: Generic configuration and contracts

**Files:** `factory/project_config.py`, `factory/snapshot.py`, `schemas/project.schema.json`, `tests/factory/test_project_config.py`, `tests/factory/test_snapshot.py`

- [x] Write failing tests for default configuration, custom path mapping, Russian brand terms, manifest hashing, drift detection, and path escape rejection.
- [x] Implement the minimum loaders and snapshot contracts.
- [x] Run the focused tests and then the factory suite.

### Task 2: Generic runtime and skills

**Files:** `.agents/skills/**`, `factory/runtime/**`, `tests/factory/**`

- [x] Port neutral fixtures and tests before changing runtime behavior.
- [x] Copy current active skills and runtime through an explicit allowlist.
- [x] Replace identity/path constants with project configuration.
- [x] Add internal `design-taste-frontend` and validate all skill metadata.
- [x] Run the complete factory suite and genericity scan.

### Task 3: Starter and bootstrap

**Files:** `templates/nextjs/**`, `bootstrap.ps1`, `factory/bootstrap.py`, `tests/bootstrap/**`

- [x] Write failing clean-room tests for New, Attach, Doctor, Update, ConfigureCodex, and Pack.
- [x] Implement dry-run/apply behavior, collision checks, backups, and lock writing.
- [x] Build the neutral Next.js starter and production Dockerfile.
- [x] Run bootstrap integration tests and starter lint/typecheck/build.

### Task 4: CI, packaging, and transfer guide

**Files:** `.github/workflows/ci.yml`, `.github/workflows/release.yml`, `docs/TRANSFER_WINDOWS.md`, `factory/dependencies.lock.json`

- [x] Add tests for ZIP manifest/checksum verification and secret/hardcode rejection.
- [x] Implement deterministic packaging and pinned dependency provenance.
- [x] Add Windows CI, Node 22/24 starter checks, and tag release workflow.
- [x] Reinstall the produced ZIP in an isolated temporary profile.

### Task 5: Release and consumer migration

- [ ] Present the verified diff and request approval for commits and remote operations.
- [ ] Publish private `v1.0.0` with release artifacts.
- [ ] Add the first project's config mapping and generic snapshot without reverting unrelated work.
- [ ] Run both factory suites and the consumer site's lint/typecheck/build.
- [ ] Request separate approval for the consumer commit; do not deploy production.
