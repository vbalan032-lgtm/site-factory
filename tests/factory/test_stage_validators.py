import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tests.factory.workspace_tempdir import workspace_tempdir


ROOT = Path(__file__).resolve().parents[2]
FACTORY = ROOT / ".agents/skills/webpage-factory"
CONTRACTS_PATH = ROOT / ".agents/skills/shared/factory-contracts/scripts/artifact_contracts.py"

STAGES = {
    "01-page-contract": "validate_stage.py",
    "02-creative-blueprint": "validate_stage.py",
    "03-conversion-copy": "validate_stage.py",
    "04-page-assets": "validate_stage.py",
    "05-full-page-build": "validate_stage.py",
    "06-integrated-qa-refinement": "validate_stage.py",
    "07-release-growth": "validate_release_transition.py",
}


class StageValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("stage_test_contracts", CONTRACTS_PATH)
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot load artifact contracts")
        cls.contracts = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.contracts
        spec.loader.exec_module(cls.contracts)

    def write_artifact(
        self,
        root: Path,
        kind: str,
        status: str,
        source_paths: list[str],
        body: str = "# Проверенный артефакт\n",
        decisions: list[dict] | None = None,
        approval: dict | None = None,
    ) -> Path:
        stage, _ = self.contracts.ARTIFACT_RULES[kind]
        fingerprints = {
            source: self.contracts.source_fingerprint(root / source, root, "1.0")
            for source in source_paths
        }
        artifact = root / self.contracts.ARTIFACT_FILENAMES[kind]
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
            f"approval: {json.dumps(approval or {'required': False, 'state': 'not_required', 'scope': 'test'}, separators=(',', ':'))}\n"
            f"next_stage_inputs: {json.dumps(sorted(self.contracts.REQUIRED_HANDOFF_INPUTS[kind]), separators=(',', ':'))}\n"
            "---\n"
            f"{body}",
            encoding="utf-8",
        )
        return artifact

    def write_page_copy(
        self,
        root: Path,
        status: str,
        source_paths: list[str],
        assets_not_needed: bool = False,
    ) -> Path:
        body = "# Текст страницы\n\nПроверенный русский текст.\n"
        decisions = [
            {
                "id": "copy_body_sha256",
                "value": "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest(),
            }
        ]
        if assets_not_needed:
            decisions.append({"id": "assets", "value": "not_needed"})
        return self.write_artifact(
            root,
            "PAGE_COPY",
            status,
            source_paths,
            body=body,
            decisions=decisions,
        )

    def write_contract_chain(self, root: Path):
        source = root / "source.md"
        source.write_text("проверенный источник", encoding="utf-8")
        contract = self.write_artifact(
            root, "PAGE_CONTRACT", "contract_ready", ["source.md"]
        )
        blueprint = self.write_artifact(
            root,
            "CREATIVE_BLUEPRINT",
            "creative_approved",
            ["PAGE_CONTRACT.md"],
            approval={"required": True, "state": "approved", "scope": "creative"},
        )
        return contract, blueprint

    def write_release_evidence(self, root: Path, mode: str, release_id: str):
        rollback = root / "rollback.json"
        rollback.write_text(
            json.dumps(
                {
                    "page_id": "page-test",
                    "route": "/test/",
                    "release_id": release_id,
                    "checkpoint": "checkpoint-1",
                    "restore_commands": ["restore factory", "restore page"],
                }
            ),
            encoding="utf-8",
        )
        history = root / "docs/system/LOOP_LOG.md"
        history.parent.mkdir(parents=True)
        previous = b"production_release release-1\n"
        transitions = {
            "production_release": ("staging_ready", "released"),
            "growth_iteration": ("released", "growth"),
            "staging_prepare": ("qa_passed", "staging_ready"),
        }
        from_status, to_status = transitions[mode]
        appended = (
            f"## {mode} {release_id}\n"
            "- page_id: page-test\n"
            "- route: /test/\n"
            f"- transition: {from_status} -> {to_status}\n"
        )
        if mode == "growth_iteration":
            appended += "- iteration_stage: 03-conversion-copy\n"
        history.write_bytes(previous + appended.encode("utf-8"))
        previous_hash = "sha256:" + hashlib.sha256(previous).hexdigest()
        return rollback, history, str(len(previous)), previous_hash

    def run_script(self, stage: str, *args: str) -> subprocess.CompletedProcess:
        script = FACTORY / stage / "scripts" / STAGES[stage]
        return subprocess.run(
            [sys.executable, str(script), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            check=False,
        )

    def test_all_stage_validator_clis_have_help(self):
        for stage in STAGES:
            with self.subTest(stage=stage):
                result = self.run_script(stage, "--help")
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_stage_one_accepts_valid_page_contract(self):
        runtime = ROOT / "tests/factory/.runtime"

        with workspace_tempdir(runtime) as tmp:
            source = tmp / "source.md"
            source.write_text("проверенный источник", encoding="utf-8")
            fixture = self.write_artifact(
                tmp, "PAGE_CONTRACT", "contract_ready", ["source.md"]
            )

            result = self.run_script(
                "01-page-contract",
                str(fixture),
                "--repo-root",
                str(tmp),
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS: PAGE_CONTRACT", result.stdout)

    def test_stage_one_rejects_draft_contract(self):
        runtime = ROOT / "tests/factory/.runtime"

        with workspace_tempdir(runtime) as tmp:
            source = tmp / "source.md"
            source.write_text("проверенный источник", encoding="utf-8")
            fixture = self.write_artifact(
                tmp, "PAGE_CONTRACT", "draft", ["source.md"]
            )
            result = self.run_script(
                "01-page-contract", str(fixture), "--repo-root", str(tmp)
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("completion status", result.stdout)

    def test_stage_two_requires_and_validates_page_contract_input(self):
        runtime = ROOT / "tests/factory/.runtime"

        with workspace_tempdir(runtime) as tmp:
            contract, blueprint = self.write_contract_chain(tmp)
            missing = self.run_script(
                "02-creative-blueprint", str(blueprint), "--repo-root", str(tmp)
            )
            valid = self.run_script(
                "02-creative-blueprint",
                str(blueprint),
                "--repo-root",
                str(tmp),
                "--input",
                str(contract),
            )

        self.assertEqual(missing.returncode, 1)
        self.assertIn("required previous-stage input", missing.stdout)
        self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)

    def test_stage_four_not_needed_requires_status_and_decision(self):
        runtime = ROOT / "tests/factory/.runtime"

        with workspace_tempdir(runtime) as tmp:
            contract, blueprint = self.write_contract_chain(tmp)
            copy = self.write_page_copy(
                tmp, "copy_ready", ["PAGE_CONTRACT.md", "CREATIVE_BLUEPRINT.md"]
            )
            invalid = self.run_script(
                "04-page-assets",
                str(copy),
                "--not-needed",
                "--repo-root",
                str(tmp),
                "--input",
                str(contract),
                "--input",
                str(blueprint),
            )
            copy = self.write_page_copy(
                tmp,
                "assets_not_needed",
                ["PAGE_CONTRACT.md", "CREATIVE_BLUEPRINT.md"],
                assets_not_needed=True,
            )
            valid = self.run_script(
                "04-page-assets",
                str(copy),
                "--not-needed",
                "--repo-root",
                str(tmp),
                "--input",
                str(contract),
                "--input",
                str(blueprint),
            )

        self.assertEqual(invalid.returncode, 1)
        self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)

    def test_stage_five_requires_asset_manifest_when_assets_are_needed(self):
        runtime = ROOT / "tests/factory/.runtime"

        with workspace_tempdir(runtime) as tmp:
            contract, blueprint = self.write_contract_chain(tmp)
            copy = self.write_page_copy(
                tmp, "copy_ready", ["PAGE_CONTRACT.md", "CREATIVE_BLUEPRINT.md"]
            )
            report = self.write_artifact(
                tmp,
                "BUILD_REPORT",
                "built",
                ["PAGE_CONTRACT.md", "CREATIVE_BLUEPRINT.md", "PAGE_COPY.md"],
            )
            result = self.run_script(
                "05-full-page-build",
                str(report),
                "--repo-root",
                str(tmp),
                "--input",
                str(contract),
                "--input",
                str(blueprint),
                "--input",
                str(copy),
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("ASSET_MANIFEST", result.stdout)

    def test_stage_five_accepts_both_optional_asset_paths(self):
        runtime = ROOT / "tests/factory/.runtime"

        with workspace_tempdir(runtime) as tmp:
            contract, blueprint = self.write_contract_chain(tmp)
            copy = self.write_page_copy(
                tmp,
                "assets_not_needed",
                ["PAGE_CONTRACT.md", "CREATIVE_BLUEPRINT.md"],
                assets_not_needed=True,
            )
            report = self.write_artifact(
                tmp,
                "BUILD_REPORT",
                "built",
                ["PAGE_CONTRACT.md", "CREATIVE_BLUEPRINT.md", "PAGE_COPY.md"],
            )
            no_assets = self.run_script(
                "05-full-page-build",
                str(report),
                "--repo-root",
                str(tmp),
                "--input",
                str(contract),
                "--input",
                str(blueprint),
                "--input",
                str(copy),
            )

            copy = self.write_page_copy(
                tmp, "copy_ready", ["PAGE_CONTRACT.md", "CREATIVE_BLUEPRINT.md"]
            )
            manifest = self.write_artifact(
                tmp,
                "ASSET_MANIFEST",
                "assets_ready",
                ["PAGE_CONTRACT.md", "CREATIVE_BLUEPRINT.md", "PAGE_COPY.md"],
            )
            report = self.write_artifact(
                tmp,
                "BUILD_REPORT",
                "built",
                [
                    "PAGE_CONTRACT.md",
                    "CREATIVE_BLUEPRINT.md",
                    "PAGE_COPY.md",
                    "ASSET_MANIFEST.md",
                ],
            )
            with_assets = self.run_script(
                "05-full-page-build",
                str(report),
                "--repo-root",
                str(tmp),
                "--input",
                str(contract),
                "--input",
                str(blueprint),
                "--input",
                str(copy),
                "--input",
                str(manifest),
            )

        self.assertEqual(no_assets.returncode, 0, no_assets.stdout + no_assets.stderr)
        self.assertEqual(
            with_assets.returncode, 0, with_assets.stdout + with_assets.stderr
        )

    def test_stage_six_accepts_complete_previous_stage_chain(self):
        runtime = ROOT / "tests/factory/.runtime"

        with workspace_tempdir(runtime) as tmp:
            contract, blueprint = self.write_contract_chain(tmp)
            copy = self.write_page_copy(
                tmp,
                "assets_not_needed",
                ["PAGE_CONTRACT.md", "CREATIVE_BLUEPRINT.md"],
                assets_not_needed=True,
            )
            report = self.write_artifact(
                tmp,
                "BUILD_REPORT",
                "built",
                ["PAGE_CONTRACT.md", "CREATIVE_BLUEPRINT.md", "PAGE_COPY.md"],
            )
            qa = self.write_artifact(
                tmp,
                "QA_REPORT",
                "qa_passed",
                [
                    "PAGE_CONTRACT.md",
                    "CREATIVE_BLUEPRINT.md",
                    "PAGE_COPY.md",
                    "BUILD_REPORT.md",
                ],
                body="# Отчёт проверки\n\nВсе обязательные проверки пройдены.\n",
            )
            result = self.run_script(
                "06-integrated-qa-refinement",
                str(qa),
                "--repo-root",
                str(tmp),
                "--input",
                str(contract),
                "--input",
                str(blueprint),
                "--input",
                str(copy),
                "--input",
                str(report),
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_stage_three_rejects_english_page_copy(self):
        fixture = ROOT / "tests/factory/fixtures/invalid-language-page-copy.md"

        result = self.run_script(
            "03-conversion-copy",
            str(fixture),
            "--repo-root",
            str(ROOT),
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("кирилли", result.stdout.lower())

    def test_stage_seven_rejects_wrong_approval_scope(self):
        runtime = ROOT / "tests/factory/.runtime"

        with workspace_tempdir(runtime) as tmp:
            approval = tmp / "approval.json"
            approval.write_text(
                json.dumps(
                    {
                        "scope": "creative",
                        "state": "approved",
                        "page_id": "page-test",
                        "route": "/test/",
                        "release_id": "release-2",
                        "approved_at": datetime.now(timezone.utc).isoformat(),
                        "expires_at": (
                            datetime.now(timezone.utc) + timedelta(hours=1)
                        ).isoformat(),
                    }
                ),
                encoding="utf-8",
            )
            rollback, history, previous_size, previous_hash = (
                self.write_release_evidence(tmp, "production_release", "release-2")
            )
            result = self.run_script(
                "07-release-growth",
                "--mode",
                "production_release",
                "--from-status",
                "staging_ready",
                "--to-status",
                "released",
                "--page-id",
                "page-test",
                "--route",
                "/test/",
                "--release-id",
                "release-2",
                "--approval-file",
                str(approval),
                "--repo-root",
                str(tmp),
                "--rollback",
                str(rollback),
                "--history-file",
                str(history),
                "--previous-history-size",
                previous_size,
                "--previous-history-sha256",
                previous_hash,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("production approval", result.stdout.lower())

    def test_stage_seven_accepts_production_approval(self):
        runtime = ROOT / "tests/factory/.runtime"

        with workspace_tempdir(runtime) as tmp:
            approval = tmp / "approval.json"
            approval.write_text(
                json.dumps(
                    {
                        "scope": "production",
                        "state": "approved",
                        "page_id": "page-test",
                        "route": "/test/",
                        "release_id": "release-2",
                        "approved_at": datetime.now(timezone.utc).isoformat(),
                        "expires_at": (
                            datetime.now(timezone.utc) + timedelta(hours=1)
                        ).isoformat(),
                    }
                ),
                encoding="utf-8",
            )
            rollback, history, previous_size, previous_hash = (
                self.write_release_evidence(tmp, "production_release", "release-2")
            )
            result = self.run_script(
                "07-release-growth",
                "--mode",
                "production_release",
                "--from-status",
                "staging_ready",
                "--to-status",
                "released",
                "--page-id",
                "page-test",
                "--route",
                "/test/",
                "--release-id",
                "release-2",
                "--approval-file",
                str(approval),
                "--repo-root",
                str(tmp),
                "--rollback",
                str(rollback),
                "--history-file",
                str(history),
                "--previous-history-size",
                previous_size,
                "--previous-history-sha256",
                previous_hash,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS", result.stdout)

    def test_stage_seven_rejects_rollback_outside_release_scope(self):
        runtime = ROOT / "tests/factory/.runtime"

        with workspace_tempdir(runtime) as tmp:
            rollback, _, _, _ = self.write_release_evidence(
                tmp, "staging_prepare", "release-2"
            )
            evidence = json.loads(rollback.read_text(encoding="utf-8"))
            evidence["page_id"] = "page-other"
            rollback.write_text(json.dumps(evidence), encoding="utf-8")
            result = self.run_script(
                "07-release-growth",
                "--mode",
                "staging_prepare",
                "--from-status",
                "qa_passed",
                "--to-status",
                "staging_ready",
                "--page-id",
                "page-test",
                "--route",
                "/test/",
                "--release-id",
                "release-2",
                "--repo-root",
                str(tmp),
                "--rollback",
                str(rollback),
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("rollback evidence page_id", result.stdout)

    def test_stage_seven_rejects_noncanonical_or_changed_history_prefix(self):
        runtime = ROOT / "tests/factory/.runtime"

        with workspace_tempdir(runtime) as tmp:
            _, history, previous_size, previous_hash = self.write_release_evidence(
                tmp, "growth_iteration", "release-2"
            )
            alternate = tmp / "alternate-history.md"
            alternate.write_bytes(history.read_bytes())
            noncanonical = self.run_script(
                "07-release-growth",
                "--mode",
                "growth_iteration",
                "--from-status",
                "released",
                "--to-status",
                "growth",
                "--page-id",
                "page-test",
                "--route",
                "/test/",
                "--release-id",
                "release-2",
                "--iteration-stage",
                "03-conversion-copy",
                "--repo-root",
                str(tmp),
                "--history-file",
                str(alternate),
                "--previous-history-size",
                previous_size,
                "--previous-history-sha256",
                previous_hash,
            )
            changed_prefix = self.run_script(
                "07-release-growth",
                "--mode",
                "growth_iteration",
                "--from-status",
                "released",
                "--to-status",
                "growth",
                "--page-id",
                "page-test",
                "--route",
                "/test/",
                "--release-id",
                "release-2",
                "--iteration-stage",
                "03-conversion-copy",
                "--repo-root",
                str(tmp),
                "--history-file",
                str(history),
                "--previous-history-size",
                previous_size,
                "--previous-history-sha256",
                "sha256:" + "0" * 64,
            )

        self.assertEqual(noncanonical.returncode, 1)
        self.assertIn("canonical", noncanonical.stdout)
        self.assertEqual(changed_prefix.returncode, 1)
        self.assertIn("prefix hash", changed_prefix.stdout)

    def test_stage_seven_rejects_history_append_without_transition_scope(self):
        runtime = ROOT / "tests/factory/.runtime"

        with workspace_tempdir(runtime) as tmp:
            _, history, previous_size, previous_hash = self.write_release_evidence(
                tmp, "growth_iteration", "release-2"
            )
            previous = history.read_bytes()[: int(previous_size)]
            history.write_bytes(previous + b"growth_iteration release-2\n")
            result = self.run_script(
                "07-release-growth",
                "--mode",
                "growth_iteration",
                "--from-status",
                "released",
                "--to-status",
                "growth",
                "--page-id",
                "page-test",
                "--route",
                "/test/",
                "--release-id",
                "release-2",
                "--iteration-stage",
                "03-conversion-copy",
                "--repo-root",
                str(tmp),
                "--history-file",
                str(history),
                "--previous-history-size",
                previous_size,
                "--previous-history-sha256",
                previous_hash,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("transition scope", result.stdout)

    def test_stage_seven_rejects_history_scope_prefix_collisions(self):
        runtime = ROOT / "tests/factory/.runtime"

        with workspace_tempdir(runtime) as tmp:
            _, history, previous_size, previous_hash = self.write_release_evidence(
                tmp, "growth_iteration", "release-2"
            )
            previous = history.read_bytes()[: int(previous_size)]
            collision = (
                "## growth_iteration release-2-other\n"
                "- page_id: page-test-other\n"
                "- route: /test/other\n"
                "- transition: released -> growth-other\n"
                "- iteration_stage: 03-conversion-copy-other\n"
            )
            history.write_bytes(previous + collision.encode("utf-8"))
            result = self.run_script(
                "07-release-growth",
                "--mode",
                "growth_iteration",
                "--from-status",
                "released",
                "--to-status",
                "growth",
                "--page-id",
                "page-test",
                "--route",
                "/test/",
                "--release-id",
                "release-2",
                "--iteration-stage",
                "03-conversion-copy",
                "--repo-root",
                str(tmp),
                "--history-file",
                str(history),
                "--previous-history-size",
                previous_size,
                "--previous-history-sha256",
                previous_hash,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("transition scope", result.stdout)

    def test_stage_seven_growth_requires_iteration_stage_and_preserved_history(self):
        runtime = ROOT / "tests/factory/.runtime"

        with workspace_tempdir(runtime) as tmp:
            _, history, previous_size, previous_hash = self.write_release_evidence(
                tmp, "growth_iteration", "release-2"
            )
            missing = self.run_script(
                "07-release-growth",
                "--mode",
                "growth_iteration",
                "--from-status",
                "released",
                "--to-status",
                "growth",
                "--page-id",
                "page-test",
                "--route",
                "/test/",
                "--release-id",
                "release-2",
                "--repo-root",
                str(tmp),
                "--history-file",
                str(history),
                "--previous-history-size",
                previous_size,
                "--previous-history-sha256",
                previous_hash,
            )
            valid = self.run_script(
                "07-release-growth",
                "--mode",
                "growth_iteration",
                "--from-status",
                "released",
                "--to-status",
                "growth",
                "--page-id",
                "page-test",
                "--route",
                "/test/",
                "--release-id",
                "release-2",
                "--iteration-stage",
                "03-conversion-copy",
                "--repo-root",
                str(tmp),
                "--history-file",
                str(history),
                "--previous-history-size",
                previous_size,
                "--previous-history-sha256",
                previous_hash,
            )

        self.assertEqual(missing.returncode, 1)
        self.assertIn("iteration_stage", missing.stdout)
        self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)


if __name__ == "__main__":
    unittest.main()
