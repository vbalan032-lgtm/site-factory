import hashlib
import importlib.util
import json
import os
import sys
import time
import unittest
from pathlib import Path

from tests.factory.workspace_tempdir import workspace_tempdir


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / ".agents/skills/shared/knowledge-graph-router/scripts"
STAGES = (
    "01-page-contract",
    "02-creative-blueprint",
    "03-conversion-copy",
    "04-page-assets",
    "05-full-page-build",
    "06-integrated-qa-refinement",
    "07-release-growth",
)


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


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


class GraphV11RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = load("graph_profile")
        cls.values = load("provider")
        cls.adapters = load("graphify_provider")

    def profile(self, root: Path):
        data = {
            "schema_version": "1.1",
            "project_id": "project-one",
            "provider": "graphify-json",
            "provider_settings_ref": None,
            "extraction_mode": "code-only",
            "knowledge_seed_paths": [],
            "benchmark_cases_path": None,
            "corpus_roots": ["docs"],
            "corpus_rules": [
                {
                    "root": "docs",
                    "source_role": "canonical",
                    "stages": list(STAGES),
                    "index_mode": "sections",
                }
            ],
            "exclude_globs": ["**/.env*", "graphify-out/**", "**/migration-archive/**"],
            "artifact_roots": ["docs/pages"],
            "output_path": "graphify-out/graph.json",
            "public_locale": "ru-RU",
            "freshness_max_age_minutes": 5,
            "entity_aliases": {},
            "ontology_extensions": [],
            "stage_budgets": {
                stage: {
                    "summary_tokens": 120,
                    "exact_tokens": 80,
                    "total_tokens": 200,
                    "top_k": 3,
                }
                for stage in STAGES
            },
        }
        path = root / "GRAPH_PROFILE.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return self.profiles.load_graph_profile(path, root)

    def write_graph(self, root: Path, nodes: list[dict], links=None) -> None:
        manifest = {
            path.resolve().relative_to(root.resolve()).as_posix(): digest(path)
            for path in sorted((root / "docs").rglob("*"))
            if path.is_file()
        }
        graph = root / "graphify-out/graph.json"
        graph.parent.mkdir(parents=True, exist_ok=True)
        graph.write_text(
            json.dumps(
                {
                    "nodes": nodes,
                    "links": links or [],
                    "factory_metadata": {
                        "schema_version": "1.1",
                        "project_id": "project-one",
                        "source_fingerprints": manifest,
                    },
                }
            ),
            encoding="utf-8",
        )

    def node(self, node_id: str, source: str, summary: str, **properties):
        return {
            "id": node_id,
            "project_id": "project-one",
            "type": properties.pop("type", "Entity"),
            "summary": summary,
            "source_file": source,
            "source_fingerprint": properties.pop("fingerprint"),
            "source_locator": properties.pop("source_locator", "heading:Evidence"),
            "source_role": properties.pop("source_role", "canonical"),
            "lifecycle_state": properties.pop("lifecycle_state", "current"),
            "properties": properties,
            "provenance": "EXTRACTED",
            "confidence_score": 1.0,
        }

    def test_query_filters_stage_route_role_and_lifecycle_before_ranking(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            source = tmp / "docs/source.md"
            source.parent.mkdir(parents=True)
            source.write_text("# Evidence\ncontext\n", encoding="utf-8")
            fingerprint = digest(source)
            nodes = [
                self.node("accepted", "docs/source.md", "product evidence", fingerprint=fingerprint, routes=["/"], stages=["01-page-contract"]),
                self.node("wrong-route", "docs/source.md", "product evidence", fingerprint=fingerprint, routes=["/product/"], stages=["01-page-contract"]),
                self.node("wrong-stage", "docs/source.md", "product evidence", fingerprint=fingerprint, routes=["/"], stages=["02-creative-blueprint"]),
                self.node("internal", "docs/source.md", "product evidence", fingerprint=fingerprint, routes=["/"], stages=["01-page-contract"], source_role="factory-internal"),
                self.node("changed", "docs/source.md", "product evidence", fingerprint=fingerprint, routes=["/"], stages=["01-page-contract"], lifecycle_state="changed_dependency"),
                self.node("migration", "docs/source.md", "product evidence", fingerprint=fingerprint, routes=["/"], stages=["01-page-contract"], lifecycle_state="migration_evidence"),
            ]
            self.write_graph(tmp, nodes)
            profile = self.profile(tmp)
            provider = self.adapters.GraphifyJsonProvider(profile, tmp)
            query = self.values.GraphQuery(
                "project-one", "01-page-contract", "product evidence", route="/"
            )
            hits = provider.query(query)

        self.assertEqual([hit.node_id for hit in hits], ["accepted"])

    def test_query_ranks_term_coverage_and_expands_one_hop_dependency(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            source = tmp / "docs/source.md"
            source.parent.mkdir(parents=True)
            source.write_text("# Evidence\ncontext\n", encoding="utf-8")
            fingerprint = digest(source)
            common = {"fingerprint": fingerprint, "routes": ["/"], "stages": ["01-page-contract"]}
            nodes = [
                self.node("best", "docs/source.md", "product evidence evidence", **common),
                self.node("partial", "docs/source.md", "evidence", **common),
                self.node("dependency", "docs/source.md", "human verification", **common),
                self.node("weak", "docs/source.md", "ai only", **common),
            ]
            self.write_graph(
                tmp,
                nodes,
                [{"source": "best", "target": "dependency", "relation": "SUPPORTED_BY", "confidence": "EXTRACTED", "confidence_score": 1.0}],
            )
            profile = self.profile(tmp)
            provider = self.adapters.GraphifyJsonProvider(profile, tmp)
            hits = provider.query(
                self.values.GraphQuery(
                    "project-one", "01-page-contract", "product evidence", route="/"
                )
            )

        self.assertEqual(hits[0].node_id, "best")
        self.assertIn("dependency", {hit.node_id for hit in hits})
        self.assertLessEqual(len(hits), 3)
        self.assertTrue(hasattr(hits[0], "relevance_score"))
        self.assertEqual(set(hits[0].matched_terms), {"product", "evidence"})
        self.assertGreater(hits[0].relevance_score, next(hit.relevance_score for hit in hits if hit.node_id == "partial"))

    def test_old_timestamp_warns_but_unchanged_fingerprints_remain_current(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            first = tmp / "docs/first.md"
            first.parent.mkdir(parents=True)
            first.write_text("# Evidence\nfirst\n", encoding="utf-8")
            second = tmp / "docs/second.md"
            second.write_text("# Evidence\nsecond\n", encoding="utf-8")
            nodes = [
                self.node("first", "docs/first.md", "first", fingerprint=digest(first), routes=["/"], stages=["01-page-contract"]),
                self.node("second", "docs/second.md", "second", fingerprint=digest(second), routes=["/"], stages=["01-page-contract"]),
            ]
            self.write_graph(tmp, nodes)
            graph = tmp / "graphify-out/graph.json"
            old = time.time() - 3600
            os.utime(graph, (old, old))
            profile = self.profile(tmp)
            provider = self.adapters.GraphifyJsonProvider(profile, tmp)

            current = provider.health(profile)
            first.write_text("# Evidence\nchanged\n", encoding="utf-8")
            degraded = provider.health(profile)

        self.assertTrue(hasattr(current, "state"))
        self.assertEqual(current.state, "current")
        self.assertTrue(current.fresh)
        self.assertTrue(any("age" in warning or "freshness" in warning for warning in current.warnings))
        self.assertEqual(degraded.state, "degraded")
        self.assertEqual(degraded.changed_sources, ("docs/first.md",))
        self.assertEqual(degraded.affected_node_ids, ("first",))
        self.assertNotIn("second", degraded.affected_node_ids)

    def test_corrupt_graph_reports_unavailable_state(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            source = tmp / "docs/source.md"
            source.parent.mkdir(parents=True)
            source.write_text("context", encoding="utf-8")
            profile = self.profile(tmp)
            graph = tmp / profile.output_path
            graph.parent.mkdir(parents=True)
            graph.write_text("not json", encoding="utf-8")
            health = self.adapters.GraphifyJsonProvider(profile, tmp).health(profile)

        self.assertTrue(hasattr(health, "state"))
        self.assertEqual(health.state, "unavailable")


if __name__ == "__main__":
    unittest.main()
