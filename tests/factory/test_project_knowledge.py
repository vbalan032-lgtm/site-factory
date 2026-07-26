import importlib.util
import json
import sys
import unittest
from pathlib import Path

from tests.factory.workspace_tempdir import workspace_tempdir


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "templates/nextjs"
SCRIPTS = ROOT / ".agents/skills/shared/knowledge-graph-router/scripts"


def load(name: str):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    if spec is None or spec.loader is None:
        raise RuntimeError(name)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class ProjectKnowledgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = load("graph_profile")
        cls.knowledge = load("project_knowledge")

    def fixture(self, root: Path, seed_project: str = "portable-site"):
        source = root / "docs/source.md"
        source.parent.mkdir(parents=True)
        source.write_text("Канонический источник", encoding="utf-8")
        seed = root / "docs/knowledge.json"
        seed.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "project_id": seed_project,
                    "nodes": [
                        {
                            "type": "Project",
                            "key": "business",
                            "label": "Business",
                            "summary": "Проверяемое описание проекта",
                            "source_path": "docs/source.md",
                            "source_location": "§1",
                            "routes": ["/"],
                            "stages": ["01-page-contract"],
                            "tags": ["positioning"],
                        },
                        {
                            "type": "Offer",
                            "key": "entry",
                            "label": "Entry",
                            "summary": "Проверяемая точка входа",
                            "source_path": "docs/source.md",
                            "source_location": "§2",
                        },
                    ],
                    "relationships": [
                        {
                            "source": "Project:business",
                            "target": "Offer:entry",
                            "relation": "HAS_OFFER",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        profile_data = {
            "schema_version": "1.0",
            "project_id": "portable-site",
            "provider": "graphify-json",
            "provider_settings_ref": None,
            "extraction_mode": "code-only",
            "knowledge_seed_paths": ["docs/knowledge.json"],
            "corpus_roots": ["docs"],
            "exclude_globs": ["**/.env*", "graphify-out/**"],
            "artifact_roots": ["docs/pages"],
            "output_path": "graphify-out/graph.json",
            "public_locale": "ru-RU",
            "freshness_max_age_minutes": 1440,
            "entity_aliases": {},
            "ontology_extensions": [],
            "stage_budgets": {"01-page-contract": 1000},
        }
        profile_path = root / "profile.json"
        profile_path.write_text(json.dumps(profile_data), encoding="utf-8")
        return self.profiles.load_graph_profile(profile_path, root), seed

    def test_loads_portable_curated_nodes_with_exact_sources(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile, _ = self.fixture(tmp)
            catalog = self.knowledge.load_project_knowledge(profile, tmp)
        self.assertEqual(len(catalog.records), 2)
        self.assertEqual(len(catalog.relationships), 1)
        self.assertTrue(all(record.source_fingerprint for record in catalog.records))
        self.assertTrue(all(record.project_id == "portable-site" for record in catalog.records))
        self.assertEqual(catalog.records[0].source_path, "docs/source.md")

    def test_rejects_cross_project_seed_and_missing_edge_endpoint(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile, seed = self.fixture(tmp, seed_project="other-site")
            with self.assertRaisesRegex(ValueError, "project_id"):
                self.knowledge.load_project_knowledge(profile, tmp)

            data = json.loads(seed.read_text(encoding="utf-8"))
            data["project_id"] = "portable-site"
            data["relationships"][0]["target"] = "Offer:missing"
            seed.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "endpoint"):
                self.knowledge.load_project_knowledge(profile, tmp)

    def test_current_project_seed_is_valid_and_not_hardcoded_in_loader(self):
        profile = self.profiles.load_graph_profile(
            TEMPLATE / "docs/system/knowledge-graph/GRAPH_PROFILE.json", TEMPLATE
        )
        catalog = self.knowledge.load_project_knowledge(profile, TEMPLATE)
        self.assertGreaterEqual(len(catalog.records), 3)
        self.assertGreaterEqual(len(catalog.relationships), 2)
        self.assertTrue(
            all(record.project_id == profile.project_id for record in catalog.records)
        )


if __name__ == "__main__":
    unittest.main()
