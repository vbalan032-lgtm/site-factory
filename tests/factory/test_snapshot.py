import unittest
from pathlib import Path

from .workspace_tempdir import workspace_tempdir


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        runtime = Path(__file__).resolve().parent / ".runtime"
        self.temp = workspace_tempdir(runtime)
        self.root = self.temp.__enter__()
        (self.root / ".agents/skills/example").mkdir(parents=True)
        (self.root / ".agents/skills/example/SKILL.md").write_text(
            "---\nname: example\ndescription: Example skill.\n---\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp.__exit__(None, None, None)

    def test_build_manifest_uses_repository_paths_and_sha256(self):
        from factory.snapshot import build_manifest

        manifest = build_manifest(self.root, [".agents/skills"])

        self.assertEqual(
            set(manifest), {".agents/skills/example/SKILL.md"}
        )
        self.assertRegex(
            manifest[".agents/skills/example/SKILL.md"], r"^sha256:[0-9a-f]{64}$"
        )

    def test_build_manifest_excludes_generated_python_bytecode(self):
        from factory.snapshot import build_manifest

        cache = self.root / ".agents/skills/example/__pycache__"
        cache.mkdir()
        (cache / "module.cpython-312.pyc").write_bytes(b"generated")
        (self.root / ".agents/skills/example/local.pyc").write_bytes(b"generated")

        manifest = build_manifest(self.root, [".agents/skills"])

        self.assertEqual(set(manifest), {".agents/skills/example/SKILL.md"})

    def test_detect_drift_reports_changed_and_missing_files(self):
        from factory.snapshot import build_manifest, detect_drift

        manifest = build_manifest(self.root, [".agents/skills"])
        skill = self.root / ".agents/skills/example/SKILL.md"
        skill.write_text("changed", encoding="utf-8")
        missing = self.root / "factory/missing.txt"
        manifest["factory/missing.txt"] = "sha256:" + "0" * 64

        drift = detect_drift(self.root, manifest)

        self.assertEqual(
            drift,
            (
                ".agents/skills/example/SKILL.md",
                "factory/missing.txt",
            ),
        )

    def test_manifest_rejects_owned_path_outside_repository(self):
        from factory.snapshot import SnapshotError, build_manifest

        with self.assertRaisesRegex(SnapshotError, "repository-relative"):
            build_manifest(self.root, ["../outside"])


if __name__ == "__main__":
    unittest.main()
