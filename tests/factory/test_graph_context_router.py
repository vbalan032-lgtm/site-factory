import hashlib
import importlib.util
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


def load_contracts():
    path = ROOT / ".agents/skills/shared/factory-contracts/scripts/artifact_contracts.py"
    spec = importlib.util.spec_from_file_location("artifact_contracts_for_graph_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("artifact_contracts")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeProvider:
    def __init__(self, values, health, hits):
        self.values = values
        self._health = health
        self._hits = hits
        self.profile = SimpleNamespace(stage_budgets={"01-page-contract": 100})

    def health(self, _profile):
        return self._health

    def query(self, _query):
        return list(self._hits)


class GraphContextRouterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.values = load("provider")
        cls.router = load("query_context")

    def request(self, exact_types=None, question="контекст"):
        query = self.values.GraphQuery(
            project_id="project-one",
            stage="01-page-contract",
            question=question,
            token_budget=100,
        )
        kwargs = {
            "query": query,
            "filesystem_allowlist": ("docs/source.md",),
        }
        if exact_types is not None:
            kwargs["require_exact_types"] = exact_types
        return self.values.ContextRequest(**kwargs)

    def hit(self, source_fingerprint, project_id="project-one", node_type="Claim"):
        return self.values.GraphContextHit(
            node_id="claim-1",
            project_id=project_id,
            node_type=node_type,
            summary="Краткое проверенное утверждение",
            source_path="docs/source.md",
            source_location=None,
            source_fingerprint=source_fingerprint,
            provenance="EXTRACTED",
            confidence=1.0,
            evidence_path=("source-1",),
        )

    def test_unavailable_graph_uses_allowlisted_filesystem_fallback(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            source = tmp / "docs/source.md"
            source.parent.mkdir(parents=True)
            source.write_text("канонический контекст", encoding="utf-8")
            health = self.values.GraphHealth(False, False, 0, 0, (), ("offline",))
            result = self.router.route_context(
                self.request(), FakeProvider(self.values, health, []), tmp
            )
        self.assertTrue(result.used_fallback)
        self.assertEqual(result.loaded_files, ("docs/source.md",))
        self.assertIn("unavailable", result.fallback_reason)

    def test_cross_project_hit_is_rejected_and_falls_back(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            source = tmp / "docs/source.md"
            source.parent.mkdir(parents=True)
            source.write_text("контекст", encoding="utf-8")
            digest = "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()
            health = self.values.GraphHealth(True, True, 1, 0, (), ())
            result = self.router.route_context(
                self.request(),
                FakeProvider(self.values, health, [self.hit(digest, "other-project")]),
                tmp,
            )
        self.assertTrue(result.used_fallback)
        self.assertEqual(result.hits, ())
        self.assertIn("cross-project", result.fallback_reason)

    def test_claim_reloads_exact_file_and_stale_hit_is_excluded(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            source = tmp / "docs/source.md"
            source.parent.mkdir(parents=True)
            source.write_text("доказательство", encoding="utf-8")
            digest = "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()
            health = self.values.GraphHealth(True, True, 1, 0, (), ())
            current = self.router.route_context(
                self.request(), FakeProvider(self.values, health, [self.hit(digest)]), tmp
            )
            stale = self.router.route_context(
                self.request(),
                FakeProvider(self.values, health, [self.hit("sha256:" + "0" * 64)]),
                tmp,
            )
        self.assertEqual(current.loaded_files, ("docs/source.md",))
        self.assertEqual(len(current.hits), 1)
        self.assertTrue(current.used_fallback)
        self.assertEqual(current.full_file_fallback_reasons, ("unresolved_locator",))
        self.assertEqual(stale.hits, ())
        self.assertTrue(stale.used_fallback)
        self.assertIn("full-file", stale.fallback_reason)
        self.assertEqual(stale.excluded_hits[0].reason, "changed_source")

    def test_accepts_canonical_artifact_fingerprint_format(self):
        runtime = ROOT / "tests/factory/.runtime"
        contracts = load_contracts()
        with workspace_tempdir(runtime) as tmp:
            source = tmp / "docs/source.md"
            source.parent.mkdir(parents=True)
            source.write_text(
                "---\nschema_version: \"1.0\"\n---\nдоказательство\n",
                encoding="utf-8",
            )
            digest = contracts.source_fingerprint(source, tmp, "1.0")
            health = self.values.GraphHealth(True, True, 1, 0, (), ())
            result = self.router.route_context(
                self.request(), FakeProvider(self.values, health, [self.hit(digest)]), tmp
            )
        self.assertTrue(result.used_fallback)
        self.assertEqual(result.full_file_fallback_reasons, ("unresolved_locator",))
        self.assertEqual(len(result.hits), 1)

    def test_stage_budget_caps_caller_budget(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            source = tmp / "docs/source.md"
            source.parent.mkdir(parents=True)
            source.write_text("контекст", encoding="utf-8")
            digest = "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()
            health = self.values.GraphHealth(True, True, 1, 0, (), ())
            hit = self.hit(digest, node_type="Entity")
            hit = self.values.GraphContextHit(
                **{**hit.__dict__, "summary": "очень длинное описание контекста для бюджета"}
            )
            provider = FakeProvider(self.values, health, [hit])
            provider.profile = SimpleNamespace(stage_budgets={"01-page-contract": 8})
            result = self.router.route_context(self.request(exact_types=()), provider, tmp)
        self.assertEqual(result.hits, ())
        self.assertLessEqual(result.estimated_tokens, 8)

    def test_sensitive_hit_outside_allowlist_is_not_accepted_as_summary(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            allowed = tmp / "docs/source.md"
            allowed.parent.mkdir(parents=True)
            allowed.write_text("разрешённый fallback", encoding="utf-8")
            protected = tmp / "docs/release.md"
            protected.write_text("release evidence", encoding="utf-8")
            digest = "sha256:" + hashlib.sha256(protected.read_bytes()).hexdigest()
            hit = self.hit(digest, node_type="ReleaseEvidence")
            hit = self.values.GraphContextHit(
                **{**hit.__dict__, "source_path": "docs/release.md"}
            )
            health = self.values.GraphHealth(True, True, 1, 0, (), ())
            result = self.router.route_context(
                self.request(), FakeProvider(self.values, health, [hit]), tmp
            )
        self.assertEqual(result.hits, ())
        self.assertTrue(result.used_fallback)
        self.assertIn("exact", result.fallback_reason)

    def test_sensitive_question_requires_exact_source_for_generic_graphify_node(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            allowed = tmp / "docs/source.md"
            allowed.parent.mkdir(parents=True)
            allowed.write_text("fallback", encoding="utf-8")
            claim = tmp / "docs/claim.md"
            claim.write_text("заявленный эффект", encoding="utf-8")
            digest = "sha256:" + hashlib.sha256(claim.read_bytes()).hexdigest()
            hit = self.hit(digest, node_type="document")
            hit = self.values.GraphContextHit(
                **{**hit.__dict__, "source_path": "docs/claim.md"}
            )
            health = self.values.GraphHealth(True, True, 1, 0, (), ())
            result = self.router.route_context(
                self.request(question="проверь claim и доказательство"),
                FakeProvider(self.values, health, [hit]),
                tmp,
            )
        self.assertEqual(result.hits, ())
        self.assertTrue(result.used_fallback)
        self.assertIn("exact", result.fallback_reason)

    def test_generic_document_with_numeric_claim_always_requires_exact_source(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            allowed = tmp / "docs/source.md"
            allowed.parent.mkdir(parents=True)
            allowed.write_text("fallback", encoding="utf-8")
            metric = tmp / "docs/metric.md"
            metric.write_text("сокращение времени на 30%", encoding="utf-8")
            digest = "sha256:" + hashlib.sha256(metric.read_bytes()).hexdigest()
            hit = self.hit(digest, node_type="document")
            hit = self.values.GraphContextHit(
                **{
                    **hit.__dict__,
                    "source_path": "docs/metric.md",
                    "summary": "сокращение времени на 30%",
                }
            )
            health = self.values.GraphHealth(True, True, 1, 0, (), ())
            result = self.router.route_context(
                self.request(question="какой эффект?"),
                FakeProvider(self.values, health, [hit]),
                tmp,
            )
        self.assertEqual(result.hits, ())
        self.assertTrue(result.used_fallback)

    def test_page_summary_can_mention_proof_without_becoming_claim_evidence(self):
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            allowed = tmp / "docs/page.md"
            allowed.parent.mkdir(parents=True)
            allowed.write_text("страница", encoding="utf-8")
            digest = "sha256:" + hashlib.sha256(allowed.read_bytes()).hexdigest()
            hit = self.hit(digest, node_type="Page")
            hit = self.values.GraphContextHit(
                **{
                    **hit.__dict__,
                    "source_path": "docs/page.md",
                    "summary": "Страница показывает доказательства и путь внедрения",
                }
            )
            health = self.values.GraphHealth(True, True, 1, 0, (), ())
            result = self.router.route_context(
                self.request(exact_types=(), question="визуальная топология страницы"),
                FakeProvider(self.values, health, [hit]),
                tmp,
            )
        self.assertFalse(result.used_fallback)
        self.assertEqual(result.loaded_files, ())
        self.assertEqual(len(result.hits), 1)


if __name__ == "__main__":
    unittest.main()
