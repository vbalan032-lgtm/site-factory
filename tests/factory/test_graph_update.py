import importlib.util
import json
import sys
import unittest
from pathlib import Path

from tests.factory.workspace_tempdir import workspace_tempdir


ROOT = Path(__file__).resolve().parents[2]
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


class GraphUpdateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = load("graph_profile")
        cls.catalogs = load("factory_catalog")
        cls.update = load("graph_update")

    def profile(self, root: Path):
        data = json.loads(
            (ROOT / "tests/factory/fixtures/graph/valid-profile.json").read_text(
                encoding="utf-8"
            )
        )
        data["corpus_roots"] = ["docs"]
        data["artifact_roots"] = ["docs/pages"]
        path = root / "profile.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return self.profiles.load_graph_profile(path, root)

    def test_materialized_corpus_applies_exclusions_before_graphify(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile = self.profile(tmp)
            files = {
                "docs/keep.md": "keep",
                "docs/.env.production": "secret",
                "docs/api-key.txt": "secret-key",
                "docs/system/skill-archive/old.md": "archive",
                "docs/system/skill-backups/old.md": "backup",
                "docs/pages/x/migration-archive/old.md": "migration",
            }
            for relative, text in files.items():
                path = tmp / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
            staging, included = self.update.materialize_profile_corpus(profile, tmp)
            kept_exists = (staging / "docs/keep.md").is_file()
            secret_exists = (staging / "docs/.env.production").exists()
        self.assertEqual(included, ("docs/keep.md",))
        self.assertTrue(kept_exists)
        self.assertFalse(secret_exists)
        self.assertNotIn("docs/api-key.txt", included)

    def test_merge_adds_project_manifest_and_deterministic_catalog(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile = self.profile(tmp)
            source = tmp / "docs/keep.md"
            source.parent.mkdir(parents=True)
            source.write_text("контекст", encoding="utf-8")
            raw = tmp / "raw.json"
            raw.write_text(
                json.dumps(
                    {
                        "nodes": [
                            {"id": "kept", "label": "Контекст", "source_file": "docs/keep.md", "file_type": "document"},
                            {"id": "outside", "label": "Secret", "source_file": "private.txt", "file_type": "document"},
                        ],
                        "links": [],
                    }
                ),
                encoding="utf-8",
            )
            catalog = self.catalogs.FactoryCatalog(
                records=(
                    self.catalogs.GraphRecord(
                        node_id="project-website:Artifact:page-contract",
                        project_id="project-website",
                        node_type="Artifact",
                        source_path="docs/keep.md",
                        source_fingerprint=None,
                        properties={"status": "contract_ready"},
                    ),
                ),
                relationships=(),
            )
            target = tmp / profile.output_path
            target.parent.mkdir()
            self.update.publish_merged_graph(raw, target, profile, tmp, catalog)
            merged = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(merged["factory_metadata"]["project_id"], "project-website")
        ids = {node["id"] for node in merged["nodes"]}
        self.assertIn("kept", ids)
        self.assertIn("project-website:Artifact:page-contract", ids)
        self.assertNotIn("outside", ids)

    def test_catalog_labels_and_edges_follow_graphify_schema(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile = self.profile(tmp)
            source = tmp / "docs/keep.md"
            source.parent.mkdir(parents=True)
            source.write_text("контекст", encoding="utf-8")
            raw = tmp / "raw.json"
            raw.write_text(json.dumps({"nodes": [], "edges": []}), encoding="utf-8")
            first = self.catalogs.GraphRecord(
                "project-website:Project:test",
                "project-website",
                "Project",
                "docs/keep.md",
                None,
                {"label": "Тестовый проект", "summary": "Описание", "source_location": "§1"},
            )
            second = self.catalogs.GraphRecord(
                "project-website:Offer:test",
                "project-website",
                "Offer",
                "docs/keep.md",
                None,
                {"label": "Оффер", "summary": "Описание"},
            )
            relation = self.catalogs.GraphRelationship(
                first.node_id, second.node_id, "HAS_OFFER", "EXTRACTED", 1.0
            )
            target = tmp / profile.output_path
            target.parent.mkdir()
            self.update.publish_merged_graph(
                raw,
                target,
                profile,
                tmp,
                self.catalogs.FactoryCatalog((first, second), (relation,)),
            )
            merged = json.loads(target.read_text(encoding="utf-8"))
        project = next(node for node in merged["nodes"] if node["id"] == first.node_id)
        edge = merged["links"][0]
        self.assertEqual(project["label"], "Тестовый проект")
        self.assertEqual(edge["source_file"], "docs/keep.md")
        self.assertEqual(edge["source_location"], "§1")

    def test_stale_versioned_source_record_is_not_republished(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile = self.profile(tmp)
            source = tmp / "docs/keep.md"
            source.parent.mkdir(parents=True)
            source.write_text("новая версия", encoding="utf-8")
            raw = tmp / "raw.json"
            raw.write_text(
                json.dumps(
                    {
                        "nodes": [
                            {
                                "id": "current-source",
                                "label": "Current",
                                "source_file": "docs/keep.md",
                                "file_type": "document",
                            }
                        ],
                        "links": [],
                    }
                ),
                encoding="utf-8",
            )
            stale = self.catalogs.GraphRecord(
                "project-website:Source:old-version",
                "project-website",
                "Source",
                "docs/keep.md",
                "sha256:" + "0" * 64,
                {"path": "docs/keep.md"},
            )
            target = tmp / profile.output_path
            target.parent.mkdir()
            self.update.publish_merged_graph(
                raw,
                target,
                profile,
                tmp,
                self.catalogs.FactoryCatalog((stale,), ()),
            )
            merged = json.loads(target.read_text(encoding="utf-8"))

        self.assertEqual(
            {node["id"] for node in merged["nodes"]}, {"current-source"}
        )

    def test_merge_preserves_connected_source_less_concept(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile = self.profile(tmp)
            source = tmp / "docs/keep.md"
            source.parent.mkdir(parents=True)
            source.write_text("контекст", encoding="utf-8")
            second = tmp / "docs/second.md"
            second.write_text("второй источник", encoding="utf-8")
            raw = tmp / "raw.json"
            raw.write_text(
                json.dumps(
                    {
                        "nodes": [
                            {"id": "source", "label": "Source", "source_file": "docs/keep.md", "file_type": "document"},
                            {"id": "source-2", "label": "Source 2", "source_file": "docs/second.md", "file_type": "document"},
                            {"id": "concept", "label": "Concept", "source_file": "", "file_type": "concept"},
                        ],
                        "links": [
                            {"source": "source", "target": "concept", "confidence": "INFERRED"},
                            {"source": "source-2", "target": "concept", "confidence": "INFERRED"}
                        ],
                    }
                ),
                encoding="utf-8",
            )
            target = tmp / profile.output_path
            target.parent.mkdir()
            empty = self.catalogs.FactoryCatalog((), ())
            self.update.publish_merged_graph(raw, target, profile, tmp, empty)
            merged = json.loads(target.read_text(encoding="utf-8"))
        concept = next(node for node in merged["nodes"] if node["id"] == "concept")
        self.assertEqual(concept["source_file"], "docs/keep.md")
        self.assertTrue(concept["source_inherited"])
        self.assertEqual(concept["evidence_sources"], ["docs/keep.md", "docs/second.md"])

    def test_unhealthy_existing_graph_does_not_block_repair(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile = self.profile(tmp)
            source = tmp / "docs/keep.md"
            source.parent.mkdir(parents=True)
            source.write_text("контекст", encoding="utf-8")
            raw = tmp / "raw.json"
            raw.write_text(
                json.dumps({"nodes": [{"id": "new", "source_file": "docs/keep.md", "label": "New"}], "links": []}),
                encoding="utf-8",
            )
            target = tmp / profile.output_path
            target.parent.mkdir()
            target.write_text(json.dumps({"nodes": [{"id": str(i)} for i in range(20)]}), encoding="utf-8")
            self.update.publish_merged_graph(
                raw, target, profile, tmp, self.catalogs.FactoryCatalog((), ())
            )
            repaired = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual({node["id"] for node in repaired["nodes"]}, {"new"})

    def test_stale_node_fingerprint_does_not_trigger_shrink_protection(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile = self.profile(tmp)
            source = tmp / "docs/keep.md"
            source.parent.mkdir(parents=True)
            source.write_text("актуальный контекст", encoding="utf-8")
            current = "sha256:" + __import__("hashlib").sha256(source.read_bytes()).hexdigest()
            raw = tmp / "raw.json"
            raw.write_text(
                json.dumps(
                    {"nodes": [{"id": "new", "source_file": "docs/keep.md"}], "links": []}
                ),
                encoding="utf-8",
            )
            target = tmp / profile.output_path
            target.parent.mkdir()
            target.write_text(
                json.dumps(
                    {
                        "nodes": [
                            {
                                "id": f"stale-{index}",
                                "project_id": profile.project_id,
                                "source_file": "docs/keep.md",
                                "source_fingerprint": "sha256:" + "0" * 64,
                            }
                            for index in range(20)
                        ],
                        "links": [],
                        "factory_metadata": {
                            "project_id": profile.project_id,
                            "source_fingerprints": {"docs/keep.md": current},
                        },
                    }
                ),
                encoding="utf-8",
            )

            self.update.publish_merged_graph(
                raw, target, profile, tmp, self.catalogs.FactoryCatalog((), ())
            )
            repaired = json.loads(target.read_text(encoding="utf-8"))

        self.assertEqual({node["id"] for node in repaired["nodes"]}, {"new"})

    def test_incremental_merge_preserves_current_unchanged_nodes(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile = self.profile(tmp)
            first = tmp / "docs/first.md"
            first.parent.mkdir(parents=True)
            first.write_text("первый", encoding="utf-8")
            second = tmp / "docs/second.md"
            second.write_text("второй", encoding="utf-8")
            target = tmp / profile.output_path
            target.parent.mkdir()
            fingerprints = {
                path.name: "sha256:" + __import__("hashlib").sha256(path.read_bytes()).hexdigest()
                for path in (first, second)
            }
            target.write_text(
                json.dumps(
                    {
                        "nodes": [
                            {"id": "first-old", "project_id": profile.project_id, "source_file": "docs/first.md", "source_fingerprint": fingerprints["first.md"]},
                            {"id": "second-old", "project_id": profile.project_id, "source_file": "docs/second.md", "source_fingerprint": fingerprints["second.md"]},
                        ],
                        "links": [{"source": "first-old", "target": "second-old", "relation": "USES"}],
                        "factory_metadata": {
                            "project_id": profile.project_id,
                            "source_fingerprints": {
                                "docs/first.md": fingerprints["first.md"],
                                "docs/second.md": fingerprints["second.md"],
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            first.write_text("первый изменён", encoding="utf-8")
            raw = tmp / "raw.json"
            raw.write_text(
                json.dumps(
                    {
                        "nodes": [{"id": "first-new", "source_file": "docs/first.md"}],
                        "edges": [],
                    }
                ),
                encoding="utf-8",
            )
            self.update.publish_merged_graph(
                raw,
                target,
                profile,
                tmp,
                self.catalogs.FactoryCatalog((), ()),
                preserve_existing=True,
            )
            merged = json.loads(target.read_text(encoding="utf-8"))
        ids = {node["id"] for node in merged["nodes"]}
        self.assertIn("first-new", ids)
        self.assertIn("second-old", ids)
        self.assertNotIn("first-old", ids)


if __name__ == "__main__":
    unittest.main()
