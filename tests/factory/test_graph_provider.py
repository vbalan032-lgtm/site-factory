import importlib.util
import hashlib
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

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


class GraphProviderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = load("graph_profile")
        cls.values = load("provider")
        cls.adapter = load("graphify_provider")

    def setup_graph(self, root: Path):
        profile_data = json.loads(
            (ROOT / "tests/factory/fixtures/graph/valid-profile.json").read_text(
                encoding="utf-8"
            )
        )
        profile_data["corpus_roots"] = ["docs"]
        profile_data["artifact_roots"] = ["docs/pages"]
        profile_path = root / "profile.json"
        profile_path.write_text(json.dumps(profile_data), encoding="utf-8")
        source = root / "docs/source.md"
        source.parent.mkdir(parents=True)
        source.write_text("точный источник", encoding="utf-8")
        graph = root / "graphify-out/graph.json"
        graph.parent.mkdir()
        nodes = [
            {
                "id": "n-inferred", "project_id": "project-website", "type": "Entity",
                "summary": "вторичный вывод", "source_path": "docs/source.md",
                "provenance": "INFERRED", "confidence": 0.8, "evidence_path": ["n-source"]
            },
            {
                "id": "n-extracted", "project_id": "project-website", "type": "Claim",
                "summary": "точный проверенный факт", "source_path": "docs/source.md",
                "provenance": "EXTRACTED", "confidence": 1.0, "evidence_path": ["n-source"]
            },
            {
                "id": "n-ambiguous", "project_id": "project-website", "type": "Entity",
                "summary": "сомнение", "source_path": "docs/source.md",
                "provenance": "AMBIGUOUS", "confidence": 0.2, "evidence_path": []
            }
        ]
        graph.write_text(json.dumps({"nodes": nodes, "edges": []}), encoding="utf-8")
        return self.profiles.load_graph_profile(profile_path, root)

    def test_query_orders_provenance_and_excludes_ambiguous(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile = self.setup_graph(tmp)
            provider = self.adapter.GraphifyJsonProvider(profile, tmp)
            query = self.values.GraphQuery(
                project_id="project-website", stage="01-page-contract",
                question="факт вывод", token_budget=100
            )
            hits = provider.query(query)
        self.assertEqual([hit.provenance for hit in hits], ["EXTRACTED", "INFERRED"])

    def test_query_filters_by_question_and_enforces_budget(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile = self.setup_graph(tmp)
            provider = self.adapter.GraphifyJsonProvider(profile, tmp)
            relevant = provider.query(
                self.values.GraphQuery(
                    project_id="project-website",
                    stage="01-page-contract",
                    question="проверенный факт",
                    token_budget=100,
                )
            )
            absent = provider.query(
                self.values.GraphQuery(
                    project_id="project-website",
                    stage="01-page-contract",
                    question="несуществующая топология",
                    token_budget=100,
                )
            )
            truncated = provider.query(
                self.values.GraphQuery(
                    project_id="project-website",
                    stage="01-page-contract",
                    question="факт вывод",
                    token_budget=6,
                )
            )
        self.assertEqual([hit.node_id for hit in relevant], ["n-extracted"])
        self.assertEqual(absent, [])
        self.assertEqual([hit.node_id for hit in truncated], ["n-extracted"])

    def test_provider_caps_budget_by_stage_profile(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile = self.setup_graph(tmp)
            profile.stage_budgets["01-page-contract"] = 6
            provider = self.adapter.GraphifyJsonProvider(profile, tmp)
            hits = provider.query(
                self.values.GraphQuery(
                    project_id="project-website",
                    stage="01-page-contract",
                    question="факт вывод",
                    token_budget=100,
                )
            )
        self.assertEqual([hit.node_id for hit in hits], ["n-extracted"])

    def test_health_handles_absent_and_corrupt_graph(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile = self.setup_graph(tmp)
            graph = tmp / profile.output_path
            graph.unlink()
            provider = self.adapter.GraphifyJsonProvider(profile, tmp)
            self.assertFalse(provider.health(profile).available)
            graph.write_text("not-json", encoding="utf-8")
            self.assertFalse(provider.health(profile).available)

    def test_update_reports_unavailable_cli_without_throwing(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile = self.setup_graph(tmp)
            provider = self.adapter.GraphifyJsonProvider(
                profile, tmp, graphify_command="definitely-missing-graphify"
            )
            health = provider.update(profile, tmp)
        self.assertFalse(health.available)
        self.assertTrue(any("unavailable" in warning for warning in health.warnings))

    def test_reads_real_graphify_node_link_schema_with_project_manifest(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile = self.setup_graph(tmp)
            source = tmp / "docs/source.md"
            digest = "sha256:" + __import__("hashlib").sha256(source.read_bytes()).hexdigest()
            graph = tmp / profile.output_path
            graph.write_text(
                json.dumps(
                    {
                        "directed": True,
                        "multigraph": False,
                        "graph": {},
                        "nodes": [
                            {
                                "id": "real-claim",
                                "label": "Проверенный факт",
                                "source_file": "docs/source.md",
                                "source_location": "1",
                                "file_type": "document",
                            },
                            {
                                "id": "real-evidence",
                                "label": "Источник",
                                "source_file": "docs/source.md",
                                "file_type": "document",
                            },
                        ],
                        "links": [
                            {
                                "source": "real-claim",
                                "target": "real-evidence",
                                "relation": "supported_by",
                                "confidence": "EXTRACTED",
                                "confidence_score": 1.0,
                            }
                        ],
                        "factory_metadata": {
                            "project_id": "project-website",
                            "source_fingerprints": {"docs/source.md": digest},
                        },
                    }
                ),
                encoding="utf-8",
            )
            provider = self.adapter.GraphifyJsonProvider(profile, tmp)
            health = provider.health(profile)
            hits = provider.query(
                self.values.GraphQuery(
                    project_id="project-website",
                    stage="01-page-contract",
                    question="проверенный факт",
                    token_budget=100,
                )
            )
        self.assertTrue(health.available, health.warnings)
        self.assertTrue(health.fresh)
        self.assertEqual([hit.node_id for hit in hits], ["real-claim"])
        self.assertEqual(hits[0].source_path, "docs/source.md")
        self.assertEqual(hits[0].provenance, "EXTRACTED")

    def test_rejects_graph_without_matching_project_manifest(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile = self.setup_graph(tmp)
            graph = tmp / profile.output_path
            data = json.loads(graph.read_text(encoding="utf-8"))
            data.pop("factory_metadata", None)
            for node in data["nodes"]:
                node.pop("project_id", None)
            graph.write_text(json.dumps(data), encoding="utf-8")
            health = self.adapter.GraphifyJsonProvider(profile, tmp).health(profile)
        self.assertFalse(health.available)
        self.assertTrue(any("project" in warning for warning in health.warnings))

    def test_health_checks_every_manifest_source_even_without_node(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile = self.setup_graph(tmp)
            source = tmp / "docs/source.md"
            digest = "sha256:" + __import__("hashlib").sha256(source.read_bytes()).hexdigest()
            graph = tmp / profile.output_path
            data = json.loads(graph.read_text(encoding="utf-8"))
            data["factory_metadata"] = {
                "project_id": "project-website",
                "source_fingerprints": {"docs/source.md": digest},
            }
            data["nodes"] = []
            graph.write_text(json.dumps(data), encoding="utf-8")
            source.write_text("changed", encoding="utf-8")
            health = self.adapter.GraphifyJsonProvider(profile, tmp).health(profile)
        self.assertTrue(health.available)
        self.assertFalse(health.fresh)
        self.assertEqual(health.stale_sources, ("docs/source.md",))

    def test_health_accepts_contract_style_fingerprint_for_canonical_source(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile = self.setup_graph(tmp)
            source = tmp / "docs/source.md"
            contracts = ROOT / ".agents/skills/shared/factory-contracts/scripts"
            if str(contracts) not in sys.path:
                sys.path.insert(0, str(contracts))
            from artifact_contracts import source_fingerprint

            graph = tmp / profile.output_path
            data = json.loads(graph.read_text(encoding="utf-8"))
            contract_digest = source_fingerprint(source, tmp, "1.0")
            data["factory_metadata"] = {
                "project_id": "project-website",
                "source_fingerprints": {
                    "docs/source.md": "sha256:" + __import__("hashlib").sha256(source.read_bytes()).hexdigest()
                },
            }
            data["nodes"] = [
                {
                    "id": "contract-source",
                    "project_id": "project-website",
                    "type": "Source",
                    "summary": "Источник контракта",
                    "source_path": "docs/source.md",
                    "source_fingerprint": contract_digest,
                }
            ]
            graph.write_text(json.dumps(data), encoding="utf-8")
            health = self.adapter.GraphifyJsonProvider(profile, tmp).health(profile)
        self.assertTrue(health.fresh, health.stale_sources)

    def test_health_detects_new_corpus_file_and_rejects_escaping_manifest_path(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile = self.setup_graph(tmp)
            source = tmp / "docs/source.md"
            digest = "sha256:" + __import__("hashlib").sha256(source.read_bytes()).hexdigest()
            graph = tmp / profile.output_path
            data = json.loads(graph.read_text(encoding="utf-8"))
            data["factory_metadata"] = {
                "project_id": "project-website",
                "source_fingerprints": {"docs/source.md": digest},
            }
            graph.write_text(json.dumps(data), encoding="utf-8")
            (tmp / "docs/new.md").write_text("new", encoding="utf-8")
            provider = self.adapter.GraphifyJsonProvider(profile, tmp)
            new_file_health = provider.health(profile)
            data["factory_metadata"]["source_fingerprints"] = {
                "../../outside.txt": "sha256:" + "0" * 64
            }
            graph.write_text(json.dumps(data), encoding="utf-8")
            escape_health = provider.health(profile)
            data["factory_metadata"]["source_fingerprints"] = {
                "docs/source.md": 123
            }
            graph.write_text(json.dumps(data), encoding="utf-8")
            malformed_health = provider.health(profile)
        self.assertFalse(new_file_health.fresh)
        self.assertIn("docs/new.md", new_file_health.stale_sources)
        self.assertFalse(escape_health.fresh)
        self.assertTrue(any("unsafe" in warning for warning in escape_health.warnings))
        self.assertFalse(malformed_health.fresh)
        self.assertTrue(
            any("malformed" in warning for warning in malformed_health.warnings)
        )

    def test_update_runs_on_staged_corpus_and_publishes_merged_manifest(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile = self.setup_graph(tmp)
            (tmp / profile.output_path).unlink()
            seen_command = []

            def runner(command, **_kwargs):
                seen_command.extend(str(part) for part in command)
                out_root = Path(command[command.index("--out") + 1])
                raw = out_root / "graphify-out/graph.json"
                raw.parent.mkdir(parents=True)
                raw.write_text(
                    json.dumps(
                        {
                            "nodes": [
                                {
                                    "id": "real-source",
                                    "label": "Источник",
                                    "source_file": "docs/source.md",
                                    "file_type": "document",
                                }
                            ],
                            "links": [],
                        }
                    ),
                    encoding="utf-8",
                )
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            provider = self.adapter.GraphifyJsonProvider(
                profile, tmp, command_runner=runner
            )
            health = provider.update(profile, tmp, incremental=True)
            published = json.loads((tmp / profile.output_path).read_text(encoding="utf-8"))
        self.assertTrue(health.available, health.warnings)
        self.assertIn(".corpus", " ".join(seen_command))
        self.assertEqual(
            published["factory_metadata"]["project_id"], "project-website"
        )

    def test_code_only_update_passes_privacy_flag(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile = self.setup_graph(tmp)
            profile = __import__("dataclasses").replace(profile, extraction_mode="code-only")
            (tmp / profile.output_path).unlink()
            seen_command = []

            def runner(command, **_kwargs):
                seen_command.extend(str(part) for part in command)
                out_root = Path(command[command.index("--out") + 1])
                raw = out_root / "graphify-out/graph.json"
                raw.parent.mkdir(parents=True)
                staged = tmp / "graphify-out/.corpus/docs/source.md"
                raw.write_text(
                    json.dumps(
                        {
                            "nodes": [
                                {
                                    "id": "code-source",
                                    "label": "Источник",
                                    "source_file": str(staged),
                                    "file_type": "code",
                                }
                            ],
                            "edges": [],
                        }
                    ),
                    encoding="utf-8",
                )
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            health = self.adapter.GraphifyJsonProvider(
                profile, tmp, command_runner=runner
            ).update(profile, tmp, incremental=False)
            published = json.loads((tmp / profile.output_path).read_text(encoding="utf-8"))
        self.assertTrue(health.available, health.warnings)
        self.assertIn("--code-only", seen_command)
        node = next(item for item in published["nodes"] if item["id"] == "code-source")
        self.assertEqual(node["source_file"], "docs/source.md")
        self.assertTrue(published["directed"])

    def test_full_update_preserves_last_healthy_graph_on_unexpected_shrink(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile = self.setup_graph(tmp)
            graph_path = tmp / profile.output_path
            fingerprint = "sha256:" + hashlib.sha256(
                (tmp / "docs/source.md").read_bytes()
            ).hexdigest()
            original = {
                "nodes": [
                    {
                        "id": node_id,
                        "project_id": profile.project_id,
                        "source_file": "docs/source.md",
                        "source_fingerprint": fingerprint,
                    }
                    for node_id in ("first-source", "second-source")
                ],
                "links": [],
                "factory_metadata": {
                    "project_id": profile.project_id,
                    "source_fingerprints": {"docs/source.md": fingerprint},
                },
            }
            graph_path.write_text(json.dumps(original), encoding="utf-8")

            def runner(command, **_kwargs):
                out_root = Path(command[command.index("--out") + 1])
                raw = out_root / "graphify-out/graph.json"
                raw.parent.mkdir(parents=True)
                raw.write_text(
                    json.dumps(
                        {
                            "nodes": [
                                {
                                    "id": "replacement-source",
                                    "source_file": "docs/source.md",
                                }
                            ],
                            "links": [],
                        }
                    ),
                    encoding="utf-8",
                )
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            health = self.adapter.GraphifyJsonProvider(
                profile, tmp, command_runner=runner
            ).update(profile, tmp, incremental=False)
            preserved = json.loads(graph_path.read_text(encoding="utf-8"))

        self.assertFalse(health.available)
        self.assertTrue(any("refusing to shrink" in warning for warning in health.warnings))
        self.assertEqual(preserved, original)


if __name__ == "__main__":
    unittest.main()
