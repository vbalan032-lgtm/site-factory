import importlib.util
import json
import sys
import unittest
from pathlib import Path

from tests.factory.workspace_tempdir import workspace_tempdir


ROOT = Path(__file__).resolve().parents[2]
PROFILE_MODULE = (
    ROOT
    / ".agents/skills/shared/knowledge-graph-router/scripts/graph_profile.py"
)
FIXTURE = ROOT / "tests/factory/fixtures/graph/valid-profile.json"


def load_module():
    spec = importlib.util.spec_from_file_location("graph_profile_under_test", PROFILE_MODULE)
    if spec is None or spec.loader is None:
        raise RuntimeError("graph_profile.py is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class GraphProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def write_profile(self, root: Path, **changes) -> Path:
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        data.update(changes)
        path = root / "GRAPH_PROFILE.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_loads_portable_valid_profile(self):
        profile = self.module.load_graph_profile(FIXTURE, ROOT)

        self.assertEqual(profile.project_id, "project-website")
        self.assertEqual(profile.provider, "graphify-json")
        self.assertEqual(profile.corpus_roots[0], "PROJECT_MASTER_CONTEXT.md")
        self.assertEqual(profile.stage_budgets["07-release-growth"], 900)
        self.assertEqual(profile.extraction_mode, "semantic")
        self.assertEqual(profile.knowledge_seed_paths, ())

    def test_loads_code_only_mode_and_seed_paths(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile_path = self.write_profile(
                tmp,
                extraction_mode="code-only",
                knowledge_seed_paths=["docs/knowledge.json"],
            )
            profile = self.module.load_graph_profile(profile_path, ROOT)
        self.assertEqual(profile.extraction_mode, "code-only")
        self.assertEqual(profile.knowledge_seed_paths, ("docs/knowledge.json",))

    def test_starter_profile_uses_v11_roles_and_all_seven_split_budgets(self):
        starter = ROOT / "templates/nextjs"
        path = starter / "docs/system/knowledge-graph/GRAPH_PROFILE.json"
        profile = self.module.load_graph_profile(path, starter)

        self.assertEqual(profile.schema_version, "1.1")
        self.assertEqual(set(profile.stage_limits), set(self.module.FACTORY_STAGES))
        self.assertEqual(
            {rule.source_role for rule in profile.corpus_rules},
            {"canonical", "design", "page_artifact", "lifecycle", "implementation"},
        )
        self.assertTrue(all(limit.total_tokens > 0 for limit in profile.stage_limits.values()))

    def test_rejects_missing_project_id_and_unknown_provider(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            missing = self.write_profile(tmp, project_id="")
            with self.assertRaisesRegex(ValueError, "project_id"):
                self.module.load_graph_profile(missing, ROOT)

            unknown = self.write_profile(tmp, provider="remote-magic")
            with self.assertRaisesRegex(ValueError, "provider"):
                self.module.load_graph_profile(unknown, ROOT)

    def test_rejects_paths_escaping_repository(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile = self.write_profile(tmp, corpus_roots=["../private"])
            with self.assertRaisesRegex(ValueError, "repository"):
                self.module.load_graph_profile(profile, ROOT)

    def test_rejects_secret_corpus_roots(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile = self.write_profile(tmp, corpus_roots=[".env.production"])
            with self.assertRaisesRegex(ValueError, "secret"):
                self.module.load_graph_profile(profile, ROOT)

    def test_rejects_output_inside_corpus_without_exclusion(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            profile = self.write_profile(
                tmp,
                corpus_roots=["docs"],
                output_path="docs/graphify-out/graph.json",
                exclude_globs=["**/.env*", "**/node_modules/**"],
            )
            with self.assertRaisesRegex(ValueError, "output"):
                self.module.load_graph_profile(profile, ROOT)


if __name__ == "__main__":
    unittest.main()
