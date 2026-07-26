import hashlib
import importlib.util
import sys
import unittest
from pathlib import Path

from tests.factory.workspace_tempdir import workspace_tempdir


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / ".agents/skills/shared/knowledge-graph-router/scripts/source_resolver.py"


def load_module():
    spec = importlib.util.spec_from_file_location("source_resolver_under_test", MODULE)
    if spec is None or spec.loader is None:
        raise RuntimeError("source_resolver.py is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SourceResolverTests(unittest.TestCase):
    def test_markdown_heading_path_resolves_exact_section_span(self):
        self.assertTrue(MODULE.is_file(), "source resolver module must exist")
        resolver = load_module()
        runtime = ROOT / "tests/factory/.runtime"
        content = (
            "# Canonical\n"
            "intro\n"
            "## Claims\n"
            "### Approved\n"
            "Exact claim evidence.\n"
            "More evidence.\n"
            "### Rejected\n"
            "Do not include.\n"
        )
        with workspace_tempdir(runtime) as tmp:
            source = tmp / "claims.md"
            source.write_text(content, encoding="utf-8")
            expected_file_hash = "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()
            result = resolver.resolve_source_slice(
                source, "heading:Canonical > Claims > Approved"
            )

        self.assertEqual(result.source_span, (4, 6))
        self.assertEqual(
            result.text, "### Approved\nExact claim evidence.\nMore evidence.\n"
        )
        self.assertEqual(
            result.file_sha256,
            expected_file_hash,
        )
        self.assertEqual(
            result.slice_sha256,
            "sha256:" + hashlib.sha256(result.text.encode("utf-8")).hexdigest(),
        )

    def test_typescript_symbol_resolves_only_balanced_declaration(self):
        self.assertTrue(MODULE.is_file(), "source resolver module must exist")
        resolver = load_module()
        runtime = ROOT / "tests/factory/.runtime"
        content = (
            "const before = 1;\n"
            "export function buildContext(value: string) {\n"
            "  if (value) {\n"
            "    return { value };\n"
            "  }\n"
            "  return null;\n"
            "}\n"
            "export function unrelated() { return before; }\n"
        )
        with workspace_tempdir(runtime) as tmp:
            source = tmp / "context.ts"
            source.write_text(content, encoding="utf-8")
            result = resolver.resolve_source_slice(source, "symbol:buildContext")

        self.assertEqual(result.source_span, (2, 7))
        self.assertIn("return { value }", result.text)
        self.assertNotIn("unrelated", result.text)

    def test_unresolvable_locator_is_an_explicit_error(self):
        self.assertTrue(MODULE.is_file(), "source resolver module must exist")
        resolver = load_module()
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            source = tmp / "source.md"
            source.write_text("# Existing\ntext\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "locator"):
                resolver.resolve_source_slice(source, "heading:Missing")

    def test_legacy_section_location_migrates_to_verified_heading_path(self):
        self.assertTrue(MODULE.is_file(), "source resolver module must exist")
        resolver = load_module()
        self.assertTrue(hasattr(resolver, "locator_from_legacy_location"))
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            source = tmp / "source.md"
            source.write_text(
                "# Canonical\n"
                "## 2. Technical claims\n"
                "### 2.1 On-premise and security\n"
                "Exact.\n",
                encoding="utf-8",
            )
            locator = resolver.locator_from_legacy_location(
                source, "В§ Technical claims / On-premise and security"
            )
            resolved = resolver.resolve_source_slice(source, locator)

        self.assertEqual(
            locator,
            "heading:Canonical > 2. Technical claims > 2.1 On-premise and security",
        )
        self.assertEqual(resolved.source_span, (3, 4))

    def test_heading_path_preserves_greater_than_inside_heading_text(self):
        resolver = load_module()
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            source = tmp / "business.md"
            source.write_text(
                "# Business\n\n## Pain -> Action -> Result\n\nEvidence.\n",
                encoding="utf-8",
            )
            resolved = resolver.resolve_source_slice(
                source,
                "heading:Business > Pain -> Action -> Result",
            )

        self.assertEqual(resolved.source_span, (3, 5))
        self.assertIn("Evidence.", resolved.text)


if __name__ == "__main__":
    unittest.main()
