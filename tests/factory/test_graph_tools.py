import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "templates/nextjs"
SCRIPTS = ROOT / ".agents/skills/shared/knowledge-graph-router/scripts"


class GraphToolTests(unittest.TestCase):
    def run_tool(self, name: str, *args: str):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / name), *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

    def test_update_and_benchmark_tools_have_help(self):
        for name in ("update_graph.py", "query_context.py", "benchmark_context.py"):
            with self.subTest(name=name):
                result = self.run_tool(name, "--help")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("usage:", result.stdout.lower())

    def test_legacy_benchmark_comparison_still_works(self):
        result = self.run_tool(
            "benchmark_context.py",
            "--filesystem-tokens",
            "1000",
            "--graph-tokens",
            "250",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"reduction_percent": 75.0', result.stdout)

    def test_update_dry_run_does_not_build_graph(self):
        output = TEMPLATE / "graphify-out/graph.json"
        before = output.read_bytes() if output.exists() else None
        result = self.run_tool(
            "update_graph.py",
            "--profile",
            str(TEMPLATE / "docs/system/knowledge-graph/GRAPH_PROFILE.json"),
            "--repo-root",
            str(TEMPLATE),
            "--incremental",
            "--dry-run",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("incremental-safe graphify extract", result.stdout)
        self.assertIn(".corpus", result.stdout)
        after = output.read_bytes() if output.exists() else None
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
