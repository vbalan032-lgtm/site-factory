import hashlib
import json
import shutil
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from workspace_tempdir import workspace_tempdir


ROOT = Path(__file__).resolve().parents[2]


class PackTests(unittest.TestCase):
    def setUp(self):
        runtime = ROOT / "tests/bootstrap/.runtime"
        self.temp = workspace_tempdir(runtime)
        self.sandbox = self.temp.__enter__()

    def tearDown(self):
        self.temp.__exit__(None, None, None)

    def test_pack_is_deterministic_and_self_verifying(self):
        from factory.bootstrap import pack_distribution, verify_package

        first = pack_distribution(ROOT, self.sandbox / "one")
        second = pack_distribution(ROOT, self.sandbox / "two")

        self.assertEqual(first.archive.read_bytes(), second.archive.read_bytes())
        self.assertTrue(verify_package(first.archive, first.checksum, first.manifest).ok)
        expected = hashlib.sha256(first.archive.read_bytes()).hexdigest()
        self.assertEqual(first.checksum.read_text(encoding="ascii").split()[0], expected)
        manifest = json.loads(first.manifest.read_text(encoding="utf-8"))
        self.assertIn("bootstrap.ps1", manifest["files"])
        with zipfile.ZipFile(first.archive) as archive:
            names = set(archive.namelist())
        self.assertIn("site-factory/bootstrap.ps1", names)
        self.assertNotIn("site-factory/.git/config", names)
        self.assertNotIn("site-factory/templates/nextjs/next-env.d.ts", names)
        self.assertNotIn("site-factory/templates/nextjs/tsconfig.tsbuildinfo", names)

    def test_pack_excludes_secret_like_and_backup_files(self):
        from factory.bootstrap import pack_distribution

        source = self.sandbox / "source"
        shutil.copytree(
            ROOT,
            source,
            ignore=shutil.ignore_patterns(
                ".git", ".tmp", ".runtime", ".next", "node_modules", "dist", "__pycache__"
            ),
        )
        (source / ".env.production").write_text("TOKEN=secret", encoding="utf-8")
        private_key = source / "docs/private-key.pem"
        private_key.write_text("PRIVATE KEY", encoding="utf-8")
        oauth = source / "factory/oauth-client-secret.json"
        oauth.write_text('{"client_secret":"secret"}', encoding="utf-8")
        password = source / "docs/passwords.txt"
        password.write_text("password=secret", encoding="utf-8")
        api_token = source / "factory/api-token.json"
        api_token.write_text('{"token":"secret"}', encoding="utf-8")
        secret_directory = source / "templates/nextjs/.secrets/config.json"
        secret_directory.parent.mkdir(parents=True)
        secret_directory.write_text('{"secret":"value"}', encoding="utf-8")
        backup = source / "templates/nextjs/.site-factory/backups/old.json"
        backup.parent.mkdir(parents=True)
        backup.write_text("private backup", encoding="utf-8")

        package = pack_distribution(source, self.sandbox / "secret-safe")
        with zipfile.ZipFile(package.archive) as archive:
            names = set(archive.namelist())

        self.assertNotIn("site-factory/.env.production", names)
        self.assertNotIn("site-factory/docs/private-key.pem", names)
        self.assertNotIn("site-factory/factory/oauth-client-secret.json", names)
        self.assertNotIn("site-factory/docs/passwords.txt", names)
        self.assertNotIn("site-factory/factory/api-token.json", names)
        self.assertNotIn("site-factory/templates/nextjs/.secrets/config.json", names)
        self.assertNotIn(
            "site-factory/templates/nextjs/.site-factory/backups/old.json", names
        )

    def test_pack_rejects_windows_junction_or_reparse_point(self):
        from factory.bootstrap import BootstrapError, pack_distribution

        with patch.object(Path, "is_junction", return_value=True):
            with self.assertRaisesRegex(BootstrapError, "reparse"):
                pack_distribution(ROOT, self.sandbox / "reparse")

    def test_verify_rejects_subset_manifest_and_extra_archive_entry(self):
        from factory.bootstrap import pack_distribution, verify_package

        package = pack_distribution(ROOT, self.sandbox / "strict")
        manifest = json.loads(package.manifest.read_text(encoding="utf-8"))
        manifest["files"].pop(next(iter(manifest["files"])))
        package.manifest.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        self.assertFalse(
            verify_package(package.archive, package.checksum, package.manifest).ok
        )

        package = pack_distribution(ROOT, self.sandbox / "strict-extra")
        with zipfile.ZipFile(package.archive, "a") as archive:
            archive.writestr("site-factory/EXTRA.txt", "unexpected")
        digest = hashlib.sha256(package.archive.read_bytes()).hexdigest()
        package.checksum.write_text(
            f"{digest}  {package.archive.name}\n", encoding="ascii"
        )
        self.assertFalse(
            verify_package(package.archive, package.checksum, package.manifest).ok
        )

    def test_pack_cli_is_dry_run_until_apply(self):
        from factory.bootstrap import main

        output = self.sandbox / "cli-dist"
        self.assertEqual(main(["pack", "--source", str(ROOT), "--output", str(output)]), 0)
        self.assertFalse(output.exists())
        self.assertEqual(
            main(
                [
                    "pack",
                    "--source",
                    str(ROOT),
                    "--output",
                    str(output),
                    "--apply",
                ]
            ),
            0,
        )
        self.assertTrue(next(output.glob("*.zip")).is_file())

    def test_release_workflow_requires_manual_approved_release_and_verifies_package(self):
        workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")

        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("tags: [\"v*\"]", workflow)
        self.assertIn("environment: release", workflow)
        self.assertIn("APPROVED_TAG: ${{ inputs.tag }}", workflow)
        self.assertNotIn("'${{ inputs.tag }}'", workflow)
        self.assertIn("$env:APPROVED_TAG", workflow)
        self.assertIn("-Mode Pack -Output dist -Apply", workflow)
        self.assertIn("-Mode Verify", workflow)
        self.assertIn("ExpectedTag", workflow)


if __name__ == "__main__":
    unittest.main()
