# Graph profile schema

## Version 1.1

Schema `1.1` keeps the portable `1.0` fields and adds two required controls:

- `corpus_rules`: one rule per declared corpus root with `source_role`, allowed `stages`, and `index_mode` (`sections`, `code-symbols`, `full`, or `excluded`);
- a split object for every one of the seven `stage_budgets`: positive `summary_tokens`, `exact_tokens`, `total_tokens`, and `top_k`, with summary plus exact not exceeding total.

Required common fields are `schema_version`, `project_id`, `provider`, `corpus_roots`, `exclude_globs`, `artifact_roots`, `output_path`, `public_locale`, `freshness_max_age_minutes`, `entity_aliases`, `ontology_extensions`, and `stage_budgets`. `provider_settings_ref` may be null. Optional `extraction_mode` is `semantic` or privacy-preserving local `code-only`; `knowledge_seed_paths` and `benchmark_cases_path` configure derived project data but do not make those files part of the page corpus.

All paths are repository-relative. Corpus and settings paths cannot escape the repository or target secrets. Generated output, `skill-archive`, `skill-backups`, and page `migration-archive` paths remain excluded. Generated output inside a corpus root requires an explicit exclusion.

Every production curated node in a `1.1` seed requires a resolvable `source_locator`. Publication materializes `source_span`, `file_sha256`, `slice_sha256`, `source_role`, `routes`, `stages`, and `lifecycle_state`. Markdown uses stable `heading:` paths; supported code uses `symbol:` locators. An unresolved production locator rejects the build.

Freshness is fingerprint-first. An old timestamp with unchanged fingerprints is a warning and health remains `current`. Changed inputs make health `degraded`, identify changed sources and affected node IDs, and invalidate only those nodes. Corrupt, unsafe, missing, or cross-project graphs are `unavailable`.

## Version 1.0 compatibility

Profiles and curated seeds at schema `1.0` continue to load. Corpus roots default to role `canonical`, all seven stages, and `full` indexing. Integer stage budgets are split 60/40 into summary/exact with `top_k: 12`. Use `scripts/migrate_graph_profile.py` to produce explicit, verified `1.1` data.

The initial provider remains `graphify-json`; another backend is introduced as a new adapter. Canonical files remain the source of truth and the graph remains a replaceable derived index.
