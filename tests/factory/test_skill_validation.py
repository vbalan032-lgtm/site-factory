import importlib.util
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
    / "validate_skills.py"
)


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_skills", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load skill validator from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SkillValidationTests(unittest.TestCase):
    def test_webpage_factory_has_exact_stage_names(self):
        validator = load_validator()

        records = validator.scan_skills(ROOT / ".agents/skills/webpage-factory")

        self.assertEqual(
            {record.name for record in records},
            {
                "01-page-contract",
                "02-creative-blueprint",
                "03-conversion-copy",
                "04-page-assets",
                "05-full-page-build",
                "06-integrated-qa-refinement",
                "07-release-growth",
            },
        )

    def test_duplicate_names_fail(self):
        validator = load_validator()
        runtime = ROOT / "tests/factory/.runtime"
        runtime.mkdir(exist_ok=True)
        with workspace_tempdir(runtime) as root:
            for folder in ("one", "two"):
                path = root / folder
                path.mkdir()
                (path / "SKILL.md").write_text(
                    "---\n"
                    "name: duplicate\n"
                    "description: Valid description.\n"
                    "---\n"
                    "# Skill\n",
                    encoding="utf-8",
                )

            errors = validator.validate_skill_root(root)

        self.assertTrue(any("duplicate" in error.lower() for error in errors))

    def test_missing_description_fails(self):
        validator = load_validator()
        runtime = ROOT / "tests/factory/.runtime"
        runtime.mkdir(exist_ok=True)
        with workspace_tempdir(runtime) as root:
            path = root / "one"
            path.mkdir()
            (path / "SKILL.md").write_text(
                "---\nname: one\n---\n# Skill\n",
                encoding="utf-8",
            )

            errors = validator.validate_skill_root(root)

        self.assertTrue(any("description" in error.lower() for error in errors))

    def test_normal_archive_routing_fails(self):
        validator = load_validator()
        runtime = ROOT / "tests/factory/.runtime"
        runtime.mkdir(exist_ok=True)
        with workspace_tempdir(runtime) as root:
            path = root / "one"
            path.mkdir()
            (path / "SKILL.md").write_text(
                "---\n"
                "name: one\n"
                "description: Valid description.\n"
                "---\n"
                "# Skill\n"
                "Normal production owner: docs/system/skill-archive/factory-v2.\n",
                encoding="utf-8",
            )

            errors = validator.validate_skill_root(root)

        self.assertTrue(any("archive" in error.lower() for error in errors))

    def test_scan_returns_skill_name_and_path(self):
        validator = load_validator()
        runtime = ROOT / "tests/factory/.runtime"
        runtime.mkdir(exist_ok=True)
        with workspace_tempdir(runtime) as root:
            path = root / "one"
            path.mkdir()
            (path / "SKILL.md").write_text(
                "---\n"
                "name: one\n"
                "description: Valid description.\n"
                "---\n"
                "# Skill\n",
                encoding="utf-8",
            )

            records = validator.scan_skills(root)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].name, "one")
        self.assertEqual(records[0].path.name, "SKILL.md")

    def test_cli_passes_valid_skill_root(self):
        runtime = ROOT / "tests/factory/.runtime"
        runtime.mkdir(exist_ok=True)
        with workspace_tempdir(runtime) as root:
            path = root / "one"
            path.mkdir()
            (path / "SKILL.md").write_text(
                "---\n"
                "name: one\n"
                "description: Valid description.\n"
                "---\n"
                "# Skill\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(MODULE_PATH), str(root)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS: 1 active skill names are unique", result.stdout)


if __name__ == "__main__":
    unittest.main()
