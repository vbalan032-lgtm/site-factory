import importlib.util
import json
import sys
import unittest
from pathlib import Path

from tests.factory.workspace_tempdir import workspace_tempdir


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / ".agents/skills/shared/knowledge-graph-router/scripts/migrate_graph_profile.py"
STAGES = (
    "01-page-contract",
    "02-creative-blueprint",
    "03-conversion-copy",
    "04-page-assets",
    "05-full-page-build",
    "06-integrated-qa-refinement",
    "07-release-growth",
)


def load_module():
    spec = importlib.util.spec_from_file_location("graph_migration_under_test", MODULE)
    if spec is None or spec.loader is None:
        raise RuntimeError("migrate_graph_profile.py is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class GraphMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_migrates_v10_profile_and_seed_to_verified_v11(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as repo:
            docs = repo / "docs"
            docs.mkdir()
            (docs / "truth.md").write_text(
                "# Canonical\n\n## Approved claim\n\nEvidence.\n",
                encoding="utf-8",
            )
            profile = {
                "schema_version": "1.0",
                "project_id": "fixture",
                "provider": "graphify-json",
                "extraction_mode": "code-only",
                "knowledge_seed_paths": ["seed.json"],
                "benchmark_cases_path": None,
                "corpus_roots": ["docs/truth.md"],
                "exclude_globs": ["**/.env*", "graphify-out/**"],
                "artifact_roots": [],
                "output_path": "graphify-out/graph.json",
                "public_locale": "en-US",
                "freshness_max_age_minutes": 1440,
                "entity_aliases": {},
                "ontology_extensions": [],
                "stage_budgets": {stage: 1000 for stage in STAGES},
            }
            seed = {
                "schema_version": "1.0",
                "project_id": "fixture",
                "nodes": [
                    {
                        "type": "Claim",
                        "key": "approved",
                        "label": "Approved claim",
                        "summary": "Evidence.",
                        "source_path": "docs/truth.md",
                        "source_location": "В§ Approved claim",
                        "routes": ["/"],
                        "stages": ["03-conversion-copy"],
                        "tags": ["claim"],
                    }
                ],
                "relationships": [],
            }

            migrated_profile = self.module.migrate_profile_data(profile)
            migrated_seed = self.module.migrate_seed_data(repo, seed, migrated_profile)

        self.assertEqual(migrated_profile["schema_version"], "1.1")
        self.assertEqual(
            migrated_profile["corpus_rules"][0],
            {
                "root": "docs/truth.md",
                "source_role": "canonical",
                "stages": list(STAGES),
                "index_mode": "sections",
            },
        )
        self.assertEqual(
            migrated_profile["stage_budgets"]["03-conversion-copy"],
            {
                "summary_tokens": 600,
                "exact_tokens": 400,
                "total_tokens": 1000,
                "top_k": 12,
            },
        )
        node = migrated_seed["nodes"][0]
        self.assertEqual(migrated_seed["schema_version"], "1.1")
        self.assertEqual(
            node["source_locator"], "heading:Canonical > Approved claim"
        )
        self.assertEqual(node["source_role"], "canonical")
        self.assertEqual(node["lifecycle_state"], "current")

    def test_rejects_unresolvable_production_locator(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as repo:
            (repo / "truth.md").write_text("# Existing\n", encoding="utf-8")
            profile = {
                "schema_version": "1.1",
                "corpus_roots": ["truth.md"],
                "corpus_rules": [
                    {
                        "root": "truth.md",
                        "source_role": "canonical",
                        "stages": list(STAGES),
                        "index_mode": "sections",
                    }
                ],
            }
            seed = {
                "schema_version": "1.0",
                "project_id": "fixture",
                "nodes": [
                    {
                        "type": "Claim",
                        "key": "missing",
                        "source_path": "truth.md",
                        "source_location": "В§ Missing",
                    }
                ],
                "relationships": [],
            }
            with self.assertRaisesRegex(ValueError, "did not resolve"):
                self.module.migrate_seed_data(repo, seed, profile)

    def test_v10_profile_with_partial_legacy_budgets_gets_all_seven_stages(self):
        profile = {
            "schema_version": "1.0",
            "corpus_roots": ["docs"],
            "stage_budgets": {
                "01-page-contract": 8000,
                "02-creative-blueprint": 7000,
                "03-conversion-copy": 7000,
                "06-integrated-qa-refinement": 5000,
            },
        }

        migrated = self.module.migrate_profile_data(profile)

        self.assertEqual(set(migrated["stage_budgets"]), set(STAGES))
        self.assertEqual(
            migrated["stage_budgets"]["04-page-assets"]["total_tokens"],
            1000,
        )


if __name__ == "__main__":
    unittest.main()
