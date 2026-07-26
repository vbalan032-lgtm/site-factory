import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "templates/nextjs/package.json"


class StarterDependencyTests(unittest.TestCase):
    def test_starter_has_patched_next_and_no_unused_cli_runtime(self):
        package = json.loads(PACKAGE.read_text(encoding="utf-8"))

        self.assertEqual(package["dependencies"]["next"], "16.2.12")
        self.assertEqual(package["devDependencies"]["eslint-config-next"], "16.2.12")
        self.assertNotIn("shadcn", package["dependencies"])
        self.assertNotIn("lucide-react", package["dependencies"])
        self.assertNotIn("class-variance-authority", package["dependencies"])
        self.assertNotIn("tw-animate-css", package["dependencies"])
        self.assertEqual(package["overrides"]["minimatch@3.1.5"], "10.2.5")
        self.assertEqual(
            package["overrides"]["minimatch@10.2.5"]["brace-expansion"], "5.0.8"
        )
        self.assertEqual(package["overrides"]["postcss"], "8.5.23")
        self.assertEqual(package["overrides"]["sharp"], "0.35.3")

    def test_starter_pins_turbopack_to_its_portable_project_root(self):
        config = (ROOT / "templates/nextjs/next.config.ts").read_text(encoding="utf-8")

        self.assertIn("turbopack:", config)
        self.assertIn("root: process.cwd()", config)


if __name__ == "__main__":
    unittest.main()
