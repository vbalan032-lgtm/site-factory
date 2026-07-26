import json
import unittest
from pathlib import Path

from .workspace_tempdir import workspace_tempdir


class ProjectConfigTests(unittest.TestCase):
    def setUp(self):
        runtime = Path(__file__).resolve().parent / ".runtime"
        self.temp = workspace_tempdir(runtime)
        self.root = self.temp.__enter__()
        (self.root / ".site-factory").mkdir()

    def tearDown(self):
        self.temp.__exit__(None, None, None)

    def write_config(self, **overrides):
        data = {
            "schema_version": "1.0",
            "project_id": "example-site",
            "project_name": "Пример",
            "public_language": "ru-Cyrl",
            "accepted_latin_terms": ["Example", "API"],
            "tech_profile": "nextjs-16",
            "paths": {
                "master_context": "PROJECT_MASTER_CONTEXT.md",
                "brand": "docs/BRAND_STYLE.md",
                "product": "docs/PRODUCT_MAP.md",
                "claims": "docs/CLAIMS_AND_PROOFS.md",
                "personas": "docs/PERSONAS.md",
                "business_architecture": "docs/BUSINESS_ARCHITECTURE.md",
                "sitemap": "docs/SITEMAP.md",
                "tech_stack": "docs/TECH_STACK.md",
                "codex_environment": "docs/CODEX_ENVIRONMENT.md",
                "source_index": "docs/source-index",
                "page_queue": "docs/site/PAGE_QUEUE.md",
                "next_task": "docs/system/NEXT_TASK.md",
                "status": "docs/system/STATUS.md",
                "loop_log": "docs/system/LOOP_LOG.md",
                "graph_profile": "docs/system/knowledge-graph/GRAPH_PROFILE.json",
                "project_knowledge": "docs/system/knowledge-graph/PROJECT_KNOWLEDGE.json",
            },
        }
        data.update(overrides)
        path = self.root / ".site-factory/project.json"
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return path

    def test_loads_project_identity_terms_and_custom_path_mapping(self):
        self.write_config(
            project_id="legacy-site",
            paths={
                **self._default_paths(),
                "master_context": "LEGACY_MASTER.md",
                "sitemap": "docs/LEGACY_SITEMAP.md",
            },
        )

        from factory.project_config import load_project_config

        config = load_project_config(self.root)

        self.assertEqual(config.project_id, "legacy-site")
        self.assertEqual(config.public_language, "ru-Cyrl")
        self.assertEqual(config.accepted_latin_terms, ("Example", "API"))
        self.assertEqual(config.path("master_context"), Path("LEGACY_MASTER.md"))
        self.assertEqual(config.path("sitemap"), Path("docs/LEGACY_SITEMAP.md"))

    def test_rejects_paths_that_escape_repository(self):
        paths = self._default_paths()
        paths["claims"] = "../private/claims.md"
        self.write_config(paths=paths)

        from factory.project_config import ProjectConfigError, load_project_config

        with self.assertRaisesRegex(ProjectConfigError, "repository-relative"):
            load_project_config(self.root)

    def test_rejects_non_russian_public_language_in_v1(self):
        self.write_config(public_language="en")

        from factory.project_config import ProjectConfigError, load_project_config

        with self.assertRaisesRegex(ProjectConfigError, "ru-Cyrl"):
            load_project_config(self.root)

    @staticmethod
    def _default_paths():
        return {
            "master_context": "PROJECT_MASTER_CONTEXT.md",
            "brand": "docs/BRAND_STYLE.md",
            "product": "docs/PRODUCT_MAP.md",
            "claims": "docs/CLAIMS_AND_PROOFS.md",
            "personas": "docs/PERSONAS.md",
            "business_architecture": "docs/BUSINESS_ARCHITECTURE.md",
            "sitemap": "docs/SITEMAP.md",
            "tech_stack": "docs/TECH_STACK.md",
            "codex_environment": "docs/CODEX_ENVIRONMENT.md",
            "source_index": "docs/source-index",
            "page_queue": "docs/site/PAGE_QUEUE.md",
            "next_task": "docs/system/NEXT_TASK.md",
            "status": "docs/system/STATUS.md",
            "loop_log": "docs/system/LOOP_LOG.md",
            "graph_profile": "docs/system/knowledge-graph/GRAPH_PROFILE.json",
            "project_knowledge": "docs/system/knowledge-graph/PROJECT_KNOWLEDGE.json",
        }


if __name__ == "__main__":
    unittest.main()
