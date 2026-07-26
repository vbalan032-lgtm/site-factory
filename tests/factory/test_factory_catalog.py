import importlib.util
import json
import sys
import unittest
from pathlib import Path

from tests.factory.workspace_tempdir import workspace_tempdir


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / ".agents/skills/shared/knowledge-graph-router/scripts"


def load_module(name: str):
    scripts = str(SCRIPTS)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"{name}_under_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"{name}.py is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FactoryCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile_module = load_module("graph_profile")
        cls.catalog_module = load_module("factory_catalog")

    def write_profile(self, root: Path, project_id: str = "second-business") -> Path:
        profile = {
            "schema_version": "1.0",
            "project_id": project_id,
            "provider": "graphify-json",
            "provider_settings_ref": None,
            "corpus_roots": ["docs"],
            "exclude_globs": [
                "**/.env*",
                "graphify-out/**",
                "docs/**/migration-archive/**",
            ],
            "artifact_roots": ["docs/pages"],
            "output_path": "graphify-out/graph.json",
            "public_locale": "ru-RU",
            "freshness_max_age_minutes": 1440,
            "entity_aliases": {},
            "ontology_extensions": [],
            "stage_budgets": {"01-page-contract": 1000},
        }
        path = root / "GRAPH_PROFILE.json"
        path.write_text(json.dumps(profile), encoding="utf-8")
        return path

    def write_artifact(
        self,
        root: Path,
        relative_path: str,
        stage: str,
        status: str,
        approval: dict,
        next_inputs: list[str],
        body: str,
        source_fingerprints: dict[str, str] | None = None,
    ) -> Path:
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "---\n"
            'schema_version: "1.0"\n'
            "page_id: page-example\n"
            "route: /example/\n"
            f"stage: {stage}\n"
            f"status: {status}\n"
            f"source_fingerprints: {json.dumps(source_fingerprints or {}, separators=(',', ':'))}\n"
            "decisions: []\n"
            "unresolved_items: []\n"
            f"approval: {json.dumps(approval, separators=(',', ':'))}\n"
            f"next_stage_inputs: {json.dumps(next_inputs, separators=(',', ':'))}\n"
            "---\n"
            f"{body}\n",
            encoding="utf-8",
        )
        return path

    def build_fixture(self, root: Path, project_id: str = "second-business"):
        profile_path = self.write_profile(root, project_id)
        source = root / "docs/source.md"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("исходные данные", encoding="utf-8")
        contract = self.write_artifact(
            root,
            "docs/pages/example/PAGE_CONTRACT.md",
            "01-page-contract",
            "contract_ready",
            {"required": False, "state": "not_required", "scope": "contract"},
            ["approved PAGE_CONTRACT.md", "source fingerprints"],
            "Контракт страницы",
            {"docs/source.md": "sha256:" + "1" * 64},
        )
        self.write_artifact(
            root,
            "docs/pages/example/CREATIVE_BLUEPRINT.md",
            "02-creative-blueprint",
            "creative_approved",
            {"required": True, "state": "approved", "scope": "creative"},
            ["approved CREATIVE_BLUEPRINT.md", "PAGE_CONTRACT.md"],
            "Творческое направление",
        )
        self.write_artifact(
            root,
            "docs/pages/example/migration-archive/PAGE_COPY.md",
            "03-conversion-copy",
            "copy_ready",
            {"required": False, "state": "not_required", "scope": "copy"},
            ["PAGE_COPY.md"],
            "Архив",
        )
        profile = self.profile_module.load_graph_profile(profile_path, root)
        return profile, contract

    def test_catalog_has_stable_ids_and_exact_lifecycle_relationships(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile, _ = self.build_fixture(tmp)
            first = self.catalog_module.build_factory_catalog(profile, tmp)
            second = self.catalog_module.build_factory_catalog(profile, tmp)

        self.assertEqual(first, second)
        ids = {record.node_id for record in first.records}
        self.assertIn("second-business:Page:page-example", ids)
        self.assertIn("second-business:Route:example", ids)
        self.assertIn("second-business:Stage:02-creative-blueprint", ids)
        self.assertIn("second-business:Status:creative-approved", ids)
        relation_types = {edge.relation_type for edge in first.relationships}
        self.assertTrue(
            {
                "ARTIFACT_FOR_PAGE",
                "PAGE_HAS_ROUTE",
                "ARTIFACT_FROM_STAGE",
                "ARTIFACT_HAS_STATUS",
                "ARTIFACT_HAS_APPROVAL",
                "ARTIFACT_REQUIRES_NEXT_INPUT",
                "ARTIFACT_USES_SOURCE",
            }.issubset(relation_types)
        )
        source_records = [
            record for record in first.records if record.node_type == "Source"
        ]
        self.assertEqual(source_records[0].source_path, "docs/source.md")
        self.assertEqual(source_records[0].source_fingerprint, "sha256:" + "1" * 64)

    def test_changed_file_changes_fingerprint_but_not_node_id(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile, contract = self.build_fixture(tmp)
            before = self.catalog_module.build_factory_catalog(profile, tmp)
            contract.write_text(
                contract.read_text(encoding="utf-8") + "\nИзменение\n",
                encoding="utf-8",
            )
            after = self.catalog_module.build_factory_catalog(profile, tmp)

        before_artifact = next(
            record
            for record in before.records
            if record.source_path.endswith("PAGE_CONTRACT.md")
        )
        after_artifact = next(
            record
            for record in after.records
            if record.source_path.endswith("PAGE_CONTRACT.md")
        )
        self.assertEqual(before_artifact.node_id, after_artifact.node_id)
        self.assertNotEqual(
            before_artifact.source_fingerprint, after_artifact.source_fingerprint
        )

    def test_mutable_implementation_snapshot_keeps_graph_source_current(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile_path = self.write_profile(tmp)
            profile_data = json.loads(profile_path.read_text(encoding="utf-8"))
            profile_data["corpus_roots"] = ["docs", "app"]
            profile_path.write_text(json.dumps(profile_data), encoding="utf-8")
            implementation = tmp / "app/page.tsx"
            implementation.parent.mkdir(parents=True)
            implementation.write_text("export default function Old() {}", encoding="utf-8")
            artifact = self.write_artifact(
                tmp,
                "docs/pages/example/PAGE_CONTRACT.md",
                "01-page-contract",
                "contract_ready",
                {"required": False, "state": "not_required", "scope": "contract"},
                ["PAGE_CONTRACT.md"],
                "Контракт страницы",
                {"app/page.tsx": "sha256:" + "0" * 64},
            )
            artifact.write_text(
                artifact.read_text(encoding="utf-8").replace(
                    "decisions: []",
                    'decisions: [{"id":"implementation_evidence","value":"preserve-not-freeze"}]',
                ),
                encoding="utf-8",
            )
            implementation.write_text("export default function New() {}", encoding="utf-8")
            profile = self.profile_module.load_graph_profile(profile_path, tmp)

            catalog = self.catalog_module.build_factory_catalog(profile, tmp)
            source = next(
                record
                for record in catalog.records
                if record.node_type == "Source" and record.source_path == "app/page.tsx"
            )

        self.assertNotEqual(source.source_fingerprint, "sha256:" + "0" * 64)
        self.assertEqual(source.properties["recorded_fingerprint"], "sha256:" + "0" * 64)
        self.assertEqual(source.properties["snapshot_state"], "historical-migration-evidence")

    def test_excludes_migration_archive_and_has_no_project_hardcode(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile, _ = self.build_fixture(tmp, project_id="second-business")
            catalog = self.catalog_module.build_factory_catalog(profile, tmp)

        serialized = repr(catalog).lower()
        self.assertNotIn("migration-archive", serialized)
        self.assertNotIn("example-site", serialized)
        self.assertTrue(
            all(record.project_id == "second-business" for record in catalog.records)
        )

    def test_catalog_connects_canonical_lifecycle_and_next_task(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile, _ = self.build_fixture(tmp)
            queue = tmp / "docs/site/PAGE_QUEUE.md"
            queue.parent.mkdir(parents=True, exist_ok=True)
            queue.write_text(
                "# PAGE_QUEUE\n\n"
                "| Page ID | Route | Priority | Status | Stage | Blocker | Iteration Stage | Notes |\n"
                "|---|---|---|---|---|---|---|---|\n"
                "| page-example | `/example/` | P0 | contract_ready | 02-creative-blueprint |  |  | migration evidence preserved |\n",
                encoding="utf-8",
            )
            task = tmp / "docs/system/NEXT_TASK.md"
            task.parent.mkdir(parents=True, exist_ok=True)
            task.write_text(
                "# NEXT_TASK\n\n"
                "- page: page-example\n"
                "- stage: 02-creative-blueprint\n"
                "- owner: webpage-factory/02-creative-blueprint\n"
                "- approval: creative_pending\n"
                "- inputs: [\"docs/pages/example/PAGE_CONTRACT.md\"]\n"
                "- output: docs/pages/example/CREATIVE_BLUEPRINT.md\n",
                encoding="utf-8",
            )
            catalog = self.catalog_module.build_factory_catalog(profile, tmp)

        records = {record.node_id: record for record in catalog.records}
        relations = {
            (edge.source_id, edge.relation_type, edge.target_id)
            for edge in catalog.relationships
        }
        page_id = "second-business:Page:page-example"
        status_id = "second-business:Status:contract-ready"
        stage_id = "second-business:Stage:02-creative-blueprint"
        task_id = next(
            record.node_id
            for record in records.values()
            if record.node_type == "NextTask"
            and record.properties.get("page") == "page-example"
        )
        source_id = next(
            record.node_id
            for record in records.values()
            if record.node_type == "Source"
            and record.source_path == "docs/source.md"
        )
        self.assertIn(status_id, records)
        self.assertIn(stage_id, records)
        self.assertIn(task_id, records)
        self.assertIn((page_id, "PAGE_HAS_STATUS", status_id), relations)
        self.assertIn((page_id, "PAGE_HAS_NEXT_STAGE", stage_id), relations)
        self.assertIn((task_id, "TASK_FOR_PAGE", page_id), relations)
        self.assertIn((task_id, "TASK_TARGETS_STAGE", stage_id), relations)
        self.assertIn((page_id, "PAGE_USES_SOURCE", source_id), relations)
        self.assertEqual(records[task_id].properties["approval"], "creative_pending")

    def test_migration_evidence_requires_explicit_catalog_mode(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile, _ = self.build_fixture(tmp)
            normal = self.catalog_module.build_factory_catalog(profile, tmp)
            diagnostic = self.catalog_module.build_factory_catalog(
                profile, tmp, migration_evidence=True
            )

        self.assertFalse(
            any(record.node_type == "MigrationEvidence" for record in normal.records)
        )
        evidence = [
            record
            for record in diagnostic.records
            if record.node_type == "MigrationEvidence"
        ]
        self.assertTrue(evidence)
        self.assertTrue(
            all("/migration-archive/" in record.source_path for record in evidence)
        )

    def test_distinct_paths_do_not_collapse_to_one_node_id(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile, _ = self.build_fixture(tmp)
            for relative in (
                "docs/pages/collision/a/b/PAGE_COPY.md",
                "docs/pages/collision/a-b/PAGE_COPY.md",
            ):
                self.write_artifact(
                    tmp,
                    relative,
                    "03-conversion-copy",
                    "copy_ready",
                    {"required": False, "state": "not_required", "scope": "copy"},
                    ["PAGE_COPY.md"],
                    "Текст",
                )
            catalog = self.catalog_module.build_factory_catalog(profile, tmp)
        collision_artifacts = [
            record
            for record in catalog.records
            if record.node_type == "Artifact" and "/collision/" in record.source_path
        ]
        self.assertEqual(len(collision_artifacts), 2)
        self.assertEqual(len({record.node_id for record in collision_artifacts}), 2)

    def test_catalog_rejects_source_paths_outside_repository(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile, contract = self.build_fixture(tmp)
            text = contract.read_text(encoding="utf-8").replace(
                'source_fingerprints: {"docs/source.md":"sha256:',
                'source_fingerprints: {"../private.txt":"sha256:',
            )
            contract.write_text(text, encoding="utf-8")
            catalog = self.catalog_module.build_factory_catalog(profile, tmp)
        self.assertFalse(
            any(record.source_path == "../private.txt" for record in catalog.records)
        )

    def test_page_and_route_keys_with_lossy_slugs_do_not_collide(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile, _ = self.build_fixture(tmp)
            paths = (
                ("docs/pages/routes/a/PAGE_COPY.md", "page-foo-bar", "/foo-bar/"),
                ("docs/pages/routes/b/PAGE_COPY.md", "page foo bar", "/foo bar/"),
            )
            for relative, page_id, route in paths:
                artifact = self.write_artifact(
                    tmp, relative, "03-conversion-copy", "copy_ready",
                    {"required": False, "state": "not_required", "scope": "copy"},
                    ["PAGE_COPY.md"], "Текст"
                )
                text = artifact.read_text(encoding="utf-8")
                text = text.replace("page_id: page-example", f"page_id: {page_id}")
                text = text.replace("route: /example/", f"route: {route}")
                artifact.write_text(text, encoding="utf-8")
            catalog = self.catalog_module.build_factory_catalog(profile, tmp)
        pages = [record for record in catalog.records if record.node_type == "Page"]
        routes = [record for record in catalog.records if record.node_type == "Route"]
        self.assertGreaterEqual(len({record.node_id for record in pages}), 3)
        self.assertGreaterEqual(len({record.node_id for record in routes}), 3)

    def test_case_only_page_and_route_keys_do_not_collide(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile, _ = self.build_fixture(tmp)
            for suffix, page_id, route in (
                ("upper", "PageFoo", "/Foo/"),
                ("lower", "pagefoo", "/foo/"),
            ):
                artifact = self.write_artifact(
                    tmp, f"docs/pages/case/{suffix}/PAGE_COPY.md",
                    "03-conversion-copy", "copy_ready",
                    {"required": False, "state": "not_required", "scope": "copy"},
                    ["PAGE_COPY.md"], "Текст"
                )
                text = artifact.read_text(encoding="utf-8")
                text = text.replace("page_id: page-example", f"page_id: {page_id}")
                text = text.replace("route: /example/", f"route: {route}")
                artifact.write_text(text, encoding="utf-8")
            catalog = self.catalog_module.build_factory_catalog(profile, tmp)
        pages = [r for r in catalog.records if r.node_type == "Page" and "pagefoo" in r.node_id.lower()]
        routes = [r for r in catalog.records if r.node_type == "Route" and "foo" in r.node_id.lower()]
        self.assertEqual(len({record.node_id for record in pages}), 2)
        self.assertEqual(len({record.node_id for record in routes}), 2)


    def test_catalog_uses_configured_lifecycle_paths(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile, _ = self.build_fixture(tmp)
            (tmp / "docs/site/PAGE_QUEUE.md").unlink(missing_ok=True)
            (tmp / "docs/system/NEXT_TASK.md").unlink(missing_ok=True)
            custom_queue = tmp / "planning/PAGES.md"
            custom_task = tmp / "planning/TASK.md"
            custom_queue.parent.mkdir(parents=True, exist_ok=True)
            custom_queue.write_text(
                "# PAGE_QUEUE\n\n"
                "| Page ID | Route | Priority | Status | Stage | Blocker | Iteration Stage | Notes |\n"
                "|---|---|---|---|---|---|---|---|\n"
                "| page-configured | `/configured/` | P0 | queued | 01-page-contract | | | |\n",
                encoding="utf-8",
            )
            custom_task.write_text(
                "# NEXT_TASK\n\n"
                "- page: page-configured\n- stage: 01-page-contract\n"
                "- owner: webpage-factory/01-page-contract\n- approval: not_required\n"
                "- inputs: []\n- output: docs/pages/configured/PAGE_CONTRACT.md\n",
                encoding="utf-8",
            )
            (tmp / ".site-factory").mkdir()
            (tmp / ".site-factory/project.json").write_text(
                json.dumps(
                    {"paths": {"page_queue": "planning/PAGES.md", "next_task": "planning/TASK.md"}}
                ),
                encoding="utf-8",
            )

            catalog = self.catalog_module.build_factory_catalog(profile, tmp)

            source_paths = {record.source_path for record in catalog.records}
            self.assertIn("planning/PAGES.md", source_paths)
            self.assertIn("planning/TASK.md", source_paths)


if __name__ == "__main__":
    unittest.main()
