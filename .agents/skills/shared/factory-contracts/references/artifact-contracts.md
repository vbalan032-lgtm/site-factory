# project v3 Artifact Contracts

## Required artifacts

Every page has exactly five required artifacts:

1. `PAGE_CONTRACT.md`
2. `CREATIVE_BLUEPRINT.md`
3. `PAGE_COPY.md`
4. `BUILD_REPORT.md`
5. `QA_REPORT.md`

`ASSET_MANIFEST.md` exists only when Stage 4 determines that managed or custom assets are required. When assets are not needed, Stage 4 changes only `PAGE_COPY.md` frontmatter to `status: assets_not_needed`; the approved copy body remains unchanged.

## Compact frontmatter

Complex values use inline JSON so the validator remains dependency-free while the frontmatter stays valid YAML.

```yaml
---
schema_version: "1.0"
page_id: page-home
route: /
stage: stage-01-page-contract
status: contract_ready
source_fingerprints: {"PROJECT_MASTER_CONTEXT.md":"sha256:<digest>"}
decisions: [{"id":"language","value":"ru-Cyrl"}]
unresolved_items: []
approval: {"required":false,"state":"not_required","scope":"contract"}
next_stage_inputs: ["PAGE_CONTRACT.md"]
---
```

All ten fields are mandatory. The artifact body must not be empty.

## Stage and status matrix

| Artifact | Stage | Valid artifact statuses |
|---|---|---|
| `PAGE_CONTRACT.md` | `stage-01-page-contract` | `draft`, `contract_ready` |
| `CREATIVE_BLUEPRINT.md` | `stage-02-creative-blueprint` | `draft`, `creative_approved` |
| `PAGE_COPY.md` | `stage-03-conversion-copy` | `draft`, `copy_ready`, `assets_not_needed` |
| `ASSET_MANIFEST.md` | `stage-04-page-assets` | `draft`, `assets_ready` |
| `BUILD_REPORT.md` | `stage-05-full-page-build` | `draft`, `built`, `blocked` |
| `QA_REPORT.md` | `stage-06-integrated-qa-refinement` | `draft`, `qa_passed`, `blocked` |

Artifact `blocked` records evidence; it does not replace the last successful page lifecycle status in `PAGE_QUEUE.md`.

Schema validation may accept `draft` and `blocked` evidence. Stage-completion validation accepts only `contract_ready`, `creative_approved`, `copy_ready`, `assets_ready`/`assets_not_needed`, `built`, or `qa_passed` for the corresponding owner stage.

## Fingerprints

Calculate SHA-256 over this exact byte sequence:

```text
normalized repository-relative path
NUL byte
raw source bytes
NUL byte
schema version encoded as UTF-8
```

Record the value as `sha256:<lowercase hex digest>`.

For a completed stage, every fingerprint key is a normalized repository-relative source path. The source must exist and the validator recomputes the digest from current bytes. Empty, malformed, missing, or stale fingerprints fail completion.

Reread the source when its fingerprint changed, artifacts conflict, a claim/proof/security/route/technical trigger applies, or the page artifact is insufficient.

## Public language

Visible website UI, navigation, copy, forms, messages, metadata, accessibility labels, alt text, and structured public answers must use Russian Cyrillic. Accepted technical and professional terms may remain Latin, including configured primary offer, configured configured domain topic, configured process method, configured domain topic, configured planning artifact, configured industry standard, ERP, MES, PLM, SCADA, SEO, GEO, API, IoT, SSR, UI, and UX.

## Approval scopes

Use distinct scopes such as `creative`, `claims`, `staging`, and `production`. An approval is valid only for its recorded scope. `creative_approved` requires creative approval; a production release requires separate production approval.

## Handoff rule

The stage validator checks the completed output and every required previous-stage artifact supplied with repeated `--input` arguments. It verifies artifact kind, final status, page ID, route, approval, and the output fingerprint recorded for each previous input. Stage 5 and 6 require `ASSET_MANIFEST.md` when `PAGE_COPY.md` is not marked `assets_not_needed`.

Completed `PAGE_COPY.md` records `copy_body_sha256`. The no-assets route also records `{"id":"assets","value":"not_needed"}`; this lets Stage 4 change lifecycle frontmatter without changing approved body copy. The Loop Engine separately validates the lifecycle transition. No failed validation may update canonical state.
