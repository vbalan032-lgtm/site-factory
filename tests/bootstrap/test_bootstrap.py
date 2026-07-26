import json
import shutil
import subprocess
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from workspace_tempdir import workspace_tempdir


ROOT = Path(__file__).resolve().parents[2]


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        runtime = ROOT / "tests/bootstrap/.runtime"
        self.temp = workspace_tempdir(runtime)
        self.sandbox = self.temp.__enter__()

    def tearDown(self):
        self.temp.__exit__(None, None, None)

    def test_new_is_dry_run_until_apply_then_creates_locked_starter(self):
        from factory.bootstrap import new_project

        target = self.sandbox / "new-site"
        preview = new_project(ROOT, target, "new-site", "Новый сайт", apply=False)
        self.assertFalse(target.exists())
        self.assertIn("create starter", preview.actions)

        result = new_project(ROOT, target, "new-site", "Новый сайт", apply=True)

        self.assertTrue(result.changed)
        self.assertTrue((target / "package.json").is_file())
        self.assertFalse((target / "node_modules").exists())
        self.assertFalse((target / ".next").exists())
        self.assertTrue((target / ".agents/skills/loop-engine/loop-daily-runner/SKILL.md").is_file())
        config = json.loads((target / ".site-factory/project.json").read_text(encoding="utf-8"))
        lock = json.loads((target / ".site-factory/lock.json").read_text(encoding="utf-8"))
        self.assertEqual(config["project_id"], "new-site")
        self.assertEqual(config["project_name"], "Новый сайт")
        graph_profile = json.loads(
            (target / config["paths"]["graph_profile"]).read_text(encoding="utf-8")
        )
        project_knowledge = json.loads(
            (target / config["paths"]["project_knowledge"]).read_text(encoding="utf-8")
        )
        self.assertEqual(graph_profile["project_id"], "new-site")
        self.assertEqual(project_knowledge["project_id"], "new-site")
        self.assertEqual(lock["factory_version"], "1.0.0")
        self.assertIn(".agents/skills/loop-engine/loop-daily-runner/SKILL.md", lock["installed_files"])

    def test_new_and_attach_validate_identity_before_writing(self):
        from factory.bootstrap import BootstrapError, attach_project, new_project

        new_target = self.sandbox / "invalid-new"
        with self.assertRaisesRegex(BootstrapError, "project_id"):
            new_project(ROOT, new_target, "INVALID ID", "Новый сайт", apply=True)
        self.assertFalse(new_target.exists())

        attach_target = self.sandbox / "invalid-attach"
        attach_target.mkdir()
        sentinel = attach_target / "keep.txt"
        sentinel.write_text("keep", encoding="utf-8")
        with self.assertRaisesRegex(BootstrapError, "project_name"):
            attach_project(ROOT, attach_target, "valid-id", "   ", apply=True)
        self.assertEqual(list(attach_target.iterdir()), [sentinel])

        occupied = self.sandbox / "occupied"
        occupied.mkdir()
        (occupied / "keep.txt").write_text("keep", encoding="utf-8")
        with self.assertRaisesRegex(BootstrapError, "absent or empty"):
            new_project(ROOT, occupied, "valid-id", "Имя", apply=False)

    def test_attach_preserves_existing_application_and_business_files(self):
        from factory.bootstrap import attach_project

        target = self.sandbox / "existing"
        (target / "app").mkdir(parents=True)
        (target / "docs").mkdir()
        sentinel = target / "app/page.tsx"
        master = target / "PROJECT_MASTER_CONTEXT.md"
        sentinel.write_text("export default function Existing() {}", encoding="utf-8")
        master.write_text("# Existing business truth", encoding="utf-8")

        attach_project(ROOT, target, "existing-site", "Существующий сайт", apply=True)

        self.assertEqual(sentinel.read_text(encoding="utf-8"), "export default function Existing() {}")
        self.assertEqual(master.read_text(encoding="utf-8"), "# Existing business truth")
        self.assertTrue((target / ".site-factory/project.json").is_file())
        self.assertTrue((target / ".agents/skills/shared/context-pack-loader/SKILL.md").is_file())

    def test_attach_refuses_collision_in_factory_owned_files(self):
        from factory.bootstrap import BootstrapError, attach_project

        target = self.sandbox / "collision"
        skill = target / ".agents/skills/loop-engine/loop-daily-runner/SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("local skill", encoding="utf-8")

        with self.assertRaisesRegex(BootstrapError, "collision"):
            attach_project(ROOT, target, "collision", "Коллизия", apply=True)

    def test_core_profile_skips_optional_ui_skills(self):
        from factory.bootstrap import new_project

        target = self.sandbox / "core-only"
        new_project(
            ROOT,
            target,
            "core-only",
            "Только ядро",
            profiles=("core",),
            apply=True,
        )

        self.assertTrue((target / ".agents/skills/webpage-factory/01-page-contract/SKILL.md").is_file())
        self.assertFalse((target / ".agents/skills/shadcn/SKILL.md").exists())
        lock = json.loads((target / ".site-factory/lock.json").read_text(encoding="utf-8"))
        self.assertEqual(lock["profiles"], ["core"])

    def test_update_replaces_clean_snapshot_and_rejects_local_drift(self):
        from factory.bootstrap import BootstrapError, new_project, update_project

        target = self.sandbox / "update"
        new_project(ROOT, target, "update-site", "Обновление", apply=True)
        source_copy = self.sandbox / "factory-copy"
        shutil.copytree(
            ROOT,
            source_copy,
            ignore=shutil.ignore_patterns(
                ".git", ".tmp", ".runtime", ".next", "node_modules", "__pycache__"
            ),
        )
        source_skill = source_copy / ".agents/skills/loop-engine/loop-daily-runner/SKILL.md"
        source_skill.write_text(source_skill.read_text(encoding="utf-8") + "\n<!-- release update -->\n", encoding="utf-8")

        update_project(source_copy, target, apply=True)
        installed = target / ".agents/skills/loop-engine/loop-daily-runner/SKILL.md"
        self.assertIn("release update", installed.read_text(encoding="utf-8"))
        backup = target / ".site-factory/backups/pre-update-1.0.0.zip"
        self.assertTrue(backup.is_file())
        with zipfile.ZipFile(backup) as archive:
            previous = archive.read(
                ".agents/skills/loop-engine/loop-daily-runner/SKILL.md"
            ).decode("utf-8")
        self.assertNotIn("release update", previous)

        installed.write_text("local drift", encoding="utf-8")
        with self.assertRaisesRegex(BootstrapError, "drift"):
            update_project(source_copy, target, apply=True)

    def test_update_rejects_new_release_collision_and_rolls_back_failure(self):
        from factory.bootstrap import BootstrapError, new_project, update_project

        target = self.sandbox / "safe-update"
        new_project(ROOT, target, "safe-update", "Безопасное обновление", apply=True)
        source_copy = self.sandbox / "factory-copy-safe"
        shutil.copytree(
            ROOT,
            source_copy,
            ignore=shutil.ignore_patterns(
                ".git", ".tmp", ".runtime", ".next", "node_modules", "dist", "__pycache__"
            ),
        )
        collision_relative = Path(
            ".agents/skills/loop-engine/loop-daily-runner/new-release-file.md"
        )
        source_collision = source_copy / collision_relative
        source_collision.write_text("factory release", encoding="utf-8")
        target_collision = target / collision_relative
        target_collision.write_text("project-owned", encoding="utf-8")

        with self.assertRaisesRegex(BootstrapError, "new release collision"):
            update_project(source_copy, target, apply=True)
        self.assertEqual(target_collision.read_text(encoding="utf-8"), "project-owned")

        target_collision.unlink()
        installed = target / ".agents/skills/loop-engine/loop-daily-runner/SKILL.md"
        original = installed.read_bytes()

        def corrupt_then_fail(*_args, **_kwargs):
            installed.write_text("partial update", encoding="utf-8")
            raise OSError("simulated copy failure")

        with patch("factory.bootstrap._copy_owned_snapshot", side_effect=corrupt_then_fail):
            with self.assertRaisesRegex(BootstrapError, "rolled back"):
                update_project(source_copy, target, apply=True)
        self.assertEqual(installed.read_bytes(), original)

    def test_doctor_reports_valid_install_and_then_drift(self):
        from factory.bootstrap import doctor, new_project

        target = self.sandbox / "doctor"
        new_project(ROOT, target, "doctor-site", "Диагностика", apply=True)
        self.assertTrue(doctor(target).ok)

        installed = target / ".agents/skills/loop-engine/loop-daily-runner/SKILL.md"
        installed.write_text("changed", encoding="utf-8")
        report = doctor(target)
        self.assertFalse(report.ok)
        self.assertTrue(any("drift" in issue for issue in report.issues))

    def test_doctor_rejects_wrong_configured_path_types(self):
        from factory.bootstrap import doctor, new_project

        target = self.sandbox / "doctor-types"
        new_project(ROOT, target, "doctor-types", "Типы путей", apply=True)
        config_path = target / ".site-factory/project.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["paths"]["master_context"] = "."
        config["paths"]["source_index"] = "PROJECT_MASTER_CONTEXT.md"
        config_path.write_text(
            json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

        report = doctor(target)
        self.assertFalse(report.ok)
        self.assertTrue(any("must be files" in issue for issue in report.issues))
        self.assertTrue(any("must be directories" in issue for issue in report.issues))

    def test_configure_codex_writes_only_project_scoped_example(self):
        from factory.bootstrap import configure_codex

        target = self.sandbox / "codex"
        preview = configure_codex(target, apply=False)
        self.assertFalse((target / ".site-factory/codex-config.example.toml").exists())
        self.assertTrue(any("project-scoped Codex example" in action for action in preview.actions))

        configure_codex(target, apply=True)
        config = target / ".site-factory/codex-config.example.toml"
        self.assertTrue(config.is_file())
        config_text = config.read_text(encoding="utf-8")
        self.assertNotIn(str(Path.home()), config_text)
        self.assertNotIn("[features]", config_text)
        self.assertNotIn("skills =", config_text)
        self.assertIn(".agents/skills", config_text)

        config.write_text("local example", encoding="utf-8")
        configure_codex(target, apply=True)
        backup = target / ".site-factory/backups/codex-config.example.toml"
        self.assertEqual(backup.read_text(encoding="utf-8"), "local example")

    def test_powershell_wrapper_maps_configure_codex_mode(self):
        target = self.sandbox / "wrapper"
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-File",
                str(ROOT / "bootstrap.ps1"),
                "-Mode",
                "ConfigureCodex",
                "-Target",
                str(target),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("DRY-RUN", result.stdout)


if __name__ == "__main__":
    unittest.main()
