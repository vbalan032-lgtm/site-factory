# Graph profile schema

Required fields: `schema_version`, `project_id`, `provider`, `corpus_roots`, `exclude_globs`, `artifact_roots`, `output_path`, `public_locale`, `freshness_max_age_minutes`, `entity_aliases`, `ontology_extensions`, and positive `stage_budgets`. `provider_settings_ref` may be null. Optional `extraction_mode` is `semantic` (default) or `code-only`; `knowledge_seed_paths` contains portable project-specific curated knowledge files. Optional `benchmark_cases_path` points to project-owned graph-vs-filesystem cases.

All paths are repository-relative. Corpus and settings paths cannot escape the repository or target secrets. Generated output, `skill-archive`, `skill-backups`, and page `migration-archive` paths remain excluded. Generated output inside a corpus root requires an explicit exclusion. The initial provider is `graphify-json`; another backend is introduced as a new adapter, not by changing page stages.

`code-only` is the privacy-preserving local mode: Graphify extracts AST relationships and the provider merges validated deterministic knowledge seeds. Seeds are derived indexes, not sources of truth; every node must point to an existing canonical source and retain its fingerprint and location. A new business replaces the profile and seed data without changing provider code.
