---
name: 04-page-assets
description: Use when an approved project page needs asset reuse, creation, or an explicit assets-not-needed handoff before the full-page build.
---

## Project configuration

Before using any project identity, accepted Latin term, or canonical path, read `.site-factory/project.json`. Resolve source-of-truth, lifecycle, and graph paths from its `paths` mapping. Project-owned sources define the brand, audience, offers, claims, and domain; never infer them from this factory skill. If the config is missing or invalid, stop and ask the owner to run Site Factory `Doctor`.


# Page Assets

Prepare only the assets required by the approved page artifacts. Prefer reuse over creation.

## Inputs

Read `PAGE_CONTRACT.md`, approved `CREATIVE_BLUEPRINT.md`, and `PAGE_COPY.md`. Load only referenced source files whose fingerprints changed or whose claims, rights, or visual requirements are unresolved.

## Workflow

1. Inventory existing project assets, components, icon libraries, diagrams, CSS treatments, and reusable SVG before proposing anything new.
2. Map every requested visual to reuse, adaptation, code-native creation, raster generation, or omission. Do not create decorative assets without a section purpose.
3. Prefer accessible HTML/CSS and precise SVG for diagrams and interface-like visuals. Use raster generation only when it materially improves the approved concept.
4. Use `canvas-design` only for conditional static art explicitly approved in the Creative Blueprint: original artistic raster/PDF hero art, motif, or poster-like section asset. Do not use it for UI, icons, ordinary diagrams, screenshots, or code-native SVG.
5. Record source, ownership or approval, intended placement, responsive dimensions, format, payload risk, and Russian alt text for every deliverable. Preserve Canvas master/provenance in `ASSET_MANIFEST.md` when used.
6. Create `ASSET_MANIFEST.md` only when the build needs a new or adapted asset. Follow `references/asset-manifest-template.md` and set the handoff status to `assets_ready` only after every required asset is available and validated.
7. If no asset work is needed, do not create a manifest. Preserve the approved body and `copy_body_sha256`; update only lifecycle frontmatter to `assets_not_needed` and add structured decision `assets=not_needed`.

Run the validator with repeated `--input` for the contract, blueprint, and copy on the manifest path. For no assets, run `PAGE_COPY.md --not-needed` with the contract and blueprint inputs. Draft or stale inputs cannot pass.

Stop on missing rights, unsupported proof visuals, unresolved source provenance, or an asset that contradicts the approved Creative Blueprint. Hand the validated artifacts to Stage 5; do not implement the page here.
