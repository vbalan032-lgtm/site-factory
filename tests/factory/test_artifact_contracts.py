import importlib.util
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

from tests.factory.workspace_tempdir import workspace_tempdir


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = (
    ROOT
    / ".agents"
    / "skills"
    / "shared"
    / "factory-contracts"
    / "scripts"
    / "artifact_contracts.py"
)


def load_contracts():
    spec = importlib.util.spec_from_file_location("artifact_contracts", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load contract runtime from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ArtifactContractTests(unittest.TestCase):
    def write_complete_artifact(
        self,
        root: Path,
        name: str,
        kind: str,
        status: str,
        source_paths: list[str],
        body: str = "# Проверенный артефакт\n",
        decisions: list[dict] | None = None,
    ) -> Path:
        contracts = load_contracts()
        stage, _ = contracts.ARTIFACT_RULES[kind]
        fingerprints = {
            source: contracts.source_fingerprint(root / source, root, "1.0")
            for source in source_paths
        }
        artifact = root / name
        artifact.write_text(
            "---\n"
            'schema_version: "1.0"\n'
            "page_id: page-test\n"
            "route: /test/\n"
            f"stage: {stage}\n"
            f"status: {status}\n"
            f"source_fingerprints: {json.dumps(fingerprints, ensure_ascii=False, separators=(',', ':'))}\n"
            f"decisions: {json.dumps(decisions or [], ensure_ascii=False, separators=(',', ':'))}\n"
            'unresolved_items: []\n'
            'approval: {"required":false,"state":"not_required","scope":"test"}\n'
            f"next_stage_inputs: {json.dumps(sorted(contracts.REQUIRED_HANDOFF_INPUTS[kind]), separators=(',', ':'))}\n"
            "---\n"
            f"{body}",
            encoding="utf-8",
        )
        return artifact

    def test_parse_compact_frontmatter(self):
        contracts = load_contracts()
        text = '''---
schema_version: "1.0"
page_id: page-home
route: /
stage: stage-01-page-contract
status: contract_ready
source_fingerprints: {"PROJECT_MASTER_CONTEXT.md":"sha256:abc"}
decisions: []
unresolved_items: []
approval: {"required":false,"state":"not_required","scope":"contract"}
next_stage_inputs: ["PAGE_CONTRACT.md"]
---
# Контракт страницы
'''

        data, body = contracts.parse_frontmatter(text)

        self.assertEqual(data["page_id"], "page-home")
        self.assertEqual(data["approval"]["state"], "not_required")
        self.assertIn("Контракт страницы", body)

    def test_parse_rejects_missing_closing_delimiter(self):
        contracts = load_contracts()

        with self.assertRaisesRegex(ValueError, "closing delimiter"):
            contracts.parse_frontmatter("---\npage_id: page-home\n")

    def test_fingerprint_changes_with_bytes_or_schema(self):
        contracts = load_contracts()
        workspace_tmp = ROOT / "tests/factory/.runtime"
        workspace_tmp.mkdir(exist_ok=True)
        with workspace_tempdir(workspace_tmp) as root:
            source = root / "source.md"
            source.write_text("первая версия", encoding="utf-8")
            first = contracts.source_fingerprint(source, root, "1.0")
            source.write_text("вторая версия", encoding="utf-8")
            second = contracts.source_fingerprint(source, root, "1.0")
            third = contracts.source_fingerprint(source, root, "1.1")

        self.assertNotEqual(first, second)
        self.assertNotEqual(second, third)
        self.assertTrue(first.startswith("sha256:"))

    def test_rejects_public_english_sentence(self):
        contracts = load_contracts()

        errors = contracts.validate_public_russian(
            "Build safer target industry workflows with artificial intelligence."
        )

        self.assertTrue(any("кирилли" in error.lower() for error in errors))

    def test_accepts_russian_with_professional_terms(self):
        contracts = load_contracts()

        errors = contracts.validate_public_russian(
            "API и SEO помогают поддерживать проверяемый цифровой продукт."
        )

        self.assertEqual(errors, [])

    def test_rejects_unapproved_latin_word_inside_russian_copy(self):
        contracts = load_contracts()

        errors = contracts.validate_public_russian(
            "Создайте smart процесс подготовки предметная методика под контролем инженера."
        )

        self.assertTrue(any("непровер" in error.lower() for error in errors))

    def test_valid_page_contract_fixture_passes(self):
        contracts = load_contracts()
        fixture = ROOT / "tests/factory/fixtures/valid-page-contract.md"

        errors = contracts.validate_artifact(fixture, "PAGE_CONTRACT", ROOT)

        self.assertEqual(errors, [])

    def test_rejects_incomplete_next_stage_handoff(self):
        contracts = load_contracts()
        runtime = ROOT / "tests/factory/.runtime"
        source = (
            ROOT / "tests/factory/fixtures/valid-page-contract.md"
        ).read_text(encoding="utf-8")
        invalid = source.replace(
            'next_stage_inputs: ["PAGE_CONTRACT.md"]',
            "next_stage_inputs: []",
        )

        with workspace_tempdir(runtime) as tmp:
            artifact = tmp / "PAGE_CONTRACT.md"
            artifact.write_text(invalid, encoding="utf-8")
            errors = contracts.validate_artifact(artifact, "PAGE_CONTRACT", ROOT)

        self.assertTrue(any("handoff" in error.lower() for error in errors))

    def test_stage_artifact_templates_use_compact_contract_frontmatter(self):
        contracts = load_contracts()
        templates = {
            "01-page-contract/references/page-contract-template.md": {
                "PAGE_CONTRACT.md"
            },
            "02-creative-blueprint/references/creative-blueprint-template.md": {
                "PAGE_CONTRACT.md",
                "CREATIVE_BLUEPRINT.md",
            },
            "03-conversion-copy/references/page-copy-template.md": {
                "PAGE_CONTRACT.md",
                "CREATIVE_BLUEPRINT.md",
                "PAGE_COPY.md",
            },
            "04-page-assets/references/asset-manifest-template.md": {
                "PAGE_CONTRACT.md",
                "CREATIVE_BLUEPRINT.md",
                "PAGE_COPY.md",
                "ASSET_MANIFEST.md",
            },
            "05-full-page-build/references/build-report-template.md": {
                "PAGE_CONTRACT.md",
                "CREATIVE_BLUEPRINT.md",
                "PAGE_COPY.md",
                "BUILD_REPORT.md",
            },
            "06-integrated-qa-refinement/references/qa-report-template.md": {
                "PAGE_CONTRACT.md",
                "CREATIVE_BLUEPRINT.md",
                "PAGE_COPY.md",
                "BUILD_REPORT.md",
                "QA_REPORT.md",
            },
        }
        root = ROOT / ".agents/skills/webpage-factory"

        for relative, required_handoff in templates.items():
            with self.subTest(template=relative):
                template = (root / relative).read_text(encoding="utf-8")
                data, _ = contracts.parse_frontmatter(template)
                self.assertEqual(
                    contracts.REQUIRED_FRONTMATTER - data.keys(),
                    set(),
                )
                self.assertIsInstance(data["source_fingerprints"], dict)
                self.assertTrue(required_handoff.issubset(data["next_stage_inputs"]))

    def test_stage_artifact_templates_pass_schema_contracts(self):
        contracts = load_contracts()
        templates = {
            "01-page-contract/references/page-contract-template.md": "PAGE_CONTRACT",
            "02-creative-blueprint/references/creative-blueprint-template.md": "CREATIVE_BLUEPRINT",
            "03-conversion-copy/references/page-copy-template.md": "PAGE_COPY",
            "04-page-assets/references/asset-manifest-template.md": "ASSET_MANIFEST",
            "05-full-page-build/references/build-report-template.md": "BUILD_REPORT",
            "06-integrated-qa-refinement/references/qa-report-template.md": "QA_REPORT",
        }
        root = ROOT / ".agents/skills/webpage-factory"
        runtime = ROOT / "tests/factory/.runtime"

        with workspace_tempdir(runtime) as tmp:
            for relative, kind in templates.items():
                with self.subTest(template=relative):
                    artifact = tmp / f"{kind}.md"
                    artifact.write_text(
                        (root / relative).read_text(encoding="utf-8"),
                        encoding="utf-8",
                    )
                    self.assertEqual(
                        contracts.validate_artifact(artifact, kind, ROOT),
                        [],
                    )

    def test_completed_stage_rejects_draft_and_blocked_statuses(self):
        contracts = load_contracts()
        runtime = ROOT / "tests/factory/.runtime"

        with workspace_tempdir(runtime) as tmp:
            source = tmp / "source.md"
            source.write_text("источник", encoding="utf-8")
            draft = self.write_complete_artifact(
                tmp, "PAGE_CONTRACT.md", "PAGE_CONTRACT", "draft", ["source.md"]
            )
            blocked = self.write_complete_artifact(
                tmp, "BUILD_REPORT.md", "BUILD_REPORT", "blocked", ["source.md"]
            )

            draft_errors = contracts.validate_completed_artifact(
                draft, "PAGE_CONTRACT", tmp, {"contract_ready"}
            )
            blocked_errors = contracts.validate_completed_artifact(
                blocked, "BUILD_REPORT", tmp, {"built"}
            )

        self.assertTrue(any("completion status" in error for error in draft_errors))
        self.assertTrue(any("completion status" in error for error in blocked_errors))

    def test_completed_stage_rejects_stale_source_fingerprint(self):
        contracts = load_contracts()
        runtime = ROOT / "tests/factory/.runtime"

        with workspace_tempdir(runtime) as tmp:
            source = tmp / "source.md"
            source.write_text("первая версия", encoding="utf-8")
            artifact = self.write_complete_artifact(
                tmp,
                "PAGE_CONTRACT.md",
                "PAGE_CONTRACT",
                "contract_ready",
                ["source.md"],
            )
            source.write_text("изменённая версия", encoding="utf-8")

            errors = contracts.validate_completed_artifact(
                artifact, "PAGE_CONTRACT", tmp, {"contract_ready"}
            )

        self.assertTrue(any("fingerprint mismatch" in error for error in errors))

    def test_page_contract_allows_changed_migration_implementation_evidence(self):
        contracts = load_contracts()
        runtime = ROOT / "tests/factory/.runtime"

        with workspace_tempdir(runtime) as tmp:
            implementation = tmp / "app/page.tsx"
            implementation.parent.mkdir(parents=True)
            implementation.write_text("export default function OldPage() {}", encoding="utf-8")
            artifact = self.write_complete_artifact(
                tmp,
                "PAGE_CONTRACT.md",
                "PAGE_CONTRACT",
                "contract_ready",
                ["app/page.tsx"],
                decisions=[
                    {"id": "implementation_evidence", "value": "preserve-not-freeze"}
                ],
            )
            implementation.write_text("export default function NewPage() {}", encoding="utf-8")

            errors = contracts.validate_completed_artifact(
                artifact, "PAGE_CONTRACT", tmp, {"contract_ready"}
            )

        self.assertEqual(errors, [])

    def test_completed_page_copy_requires_matching_body_fingerprint(self):
        contracts = load_contracts()
        runtime = ROOT / "tests/factory/.runtime"
        body = "# Текст страницы\n\nПроверенный русский текст.\n"

        with workspace_tempdir(runtime) as tmp:
            source = tmp / "source.md"
            source.write_text("источник", encoding="utf-8")
            artifact = self.write_complete_artifact(
                tmp,
                "PAGE_COPY.md",
                "PAGE_COPY",
                "copy_ready",
                ["source.md"],
                body=body,
                decisions=[{"id": "copy_body_sha256", "value": "sha256:" + "0" * 64}],
            )

            errors = contracts.validate_completed_artifact(
                artifact, "PAGE_COPY", tmp, {"copy_ready"}
            )

        self.assertTrue(any("copy body fingerprint" in error for error in errors))

        expected = "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()
        self.assertRegex(expected, r"^sha256:[0-9a-f]{64}$")

    def test_assets_not_needed_requires_decision_on_every_validation(self):
        contracts = load_contracts()
        runtime = ROOT / "tests/factory/.runtime"
        body = "# Текст страницы\n\nПроверенный русский текст.\n"
        body_hash = "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()

        with workspace_tempdir(runtime) as tmp:
            source = tmp / "source.md"
            source.write_text("источник", encoding="utf-8")
            artifact = self.write_complete_artifact(
                tmp,
                "PAGE_COPY.md",
                "PAGE_COPY",
                "assets_not_needed",
                ["source.md"],
                body=body,
                decisions=[{"id": "copy_body_sha256", "value": body_hash}],
            )
            errors = contracts.validate_completed_artifact(
                artifact, "PAGE_COPY", tmp, {"assets_not_needed"}
            )

        self.assertTrue(any("assets=not_needed" in error for error in errors))

    def test_completed_artifact_requires_canonical_filename(self):
        contracts = load_contracts()
        runtime = ROOT / "tests/factory/.runtime"

        with workspace_tempdir(runtime) as tmp:
            source = tmp / "source.md"
            source.write_text("источник", encoding="utf-8")
            artifact = self.write_complete_artifact(
                tmp, "OTHER.md", "PAGE_CONTRACT", "contract_ready", ["source.md"]
            )
            errors = contracts.validate_completed_artifact(
                artifact, "PAGE_CONTRACT", tmp, {"contract_ready"}
            )

        self.assertTrue(any("canonical artifact filename" in error for error in errors))

    def test_invalid_language_page_copy_fixture_fails(self):
        contracts = load_contracts()
        fixture = ROOT / "tests/factory/fixtures/invalid-language-page-copy.md"

        errors = contracts.validate_artifact(fixture, "PAGE_COPY", ROOT)

        self.assertTrue(any("кирилли" in error.lower() for error in errors))

    def test_public_russian_allows_project_brand_term(self):
        contracts = load_contracts()

        errors = contracts.validate_public_russian(
            "project — отраслевые ИИ-эксперты для целевой отрасли."
        )

        self.assertEqual(errors, [])

    def test_cli_validates_page_contract_fixture(self):
        script = MODULE_PATH.with_name("validate_artifact.py")
        fixture = ROOT / "tests/factory/fixtures/valid-page-contract.md"

        result = subprocess.run(
            [
                sys.executable,
                str(script),
                str(fixture),
                "--kind",
                "PAGE_CONTRACT",
                "--repo-root",
                str(ROOT),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS: PAGE_CONTRACT", result.stdout)


    def test_artifact_accepts_project_configured_brand_term(self):
        contracts = load_contracts()
        workspace_tmp = ROOT / "tests/factory/.runtime"
        workspace_tmp.mkdir(exist_ok=True)
        with workspace_tempdir(workspace_tmp) as root:
            (root / ".site-factory").mkdir()
            (root / ".site-factory/project.json").write_text(
                json.dumps({"accepted_latin_terms": ["NovaBrand"]}),
                encoding="utf-8",
            )
            source = root / "source.md"
            source.write_text("source", encoding="utf-8")
            artifact = self.write_complete_artifact(
                root,
                "PAGE_COPY.md",
                "PAGE_COPY",
                "copy_ready",
                ["source.md"],
                body="# NovaBrand\n\nРусский текст о продукте.\n",
            )

            errors = contracts.validate_artifact(artifact, "PAGE_COPY", root)

        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
