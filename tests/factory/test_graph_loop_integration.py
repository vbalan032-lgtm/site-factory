import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

from tests.factory.workspace_tempdir import workspace_tempdir


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".agents/skills/loop-engine/scripts/update_knowledge_graph.py"


def load_graph_loop():
    spec = importlib.util.spec_from_file_location("graph_loop", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load graph loop integration from {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class GraphLoopIntegrationTests(unittest.TestCase):
    def test_only_validated_macro_handoff_requests_incremental_update(self):
        graph_loop = load_graph_loop()

        self.assertTrue(
            graph_loop.should_update("validated_stage_handoff", artifact_validated=True)
        )
        self.assertFalse(graph_loop.should_update("state_only", artifact_validated=True))
        self.assertFalse(
            graph_loop.should_update("validated_stage_handoff", artifact_validated=False)
        )

    def test_failed_update_records_stale_without_touching_page_state(self):
        graph_loop = load_graph_loop()
        runtime = ROOT / "tests/factory/.runtime"
        runtime.mkdir(exist_ok=True)
        with workspace_tempdir(runtime) as tmp:
            page_state = tmp / "PAGE_QUEUE.md"
            page_state.write_text("canonical-state\n", encoding="utf-8")
            status_path = tmp / "GRAPH_STATUS.json"

            def failing_runner(*args, **kwargs):
                return subprocess.CompletedProcess(args[0], 1, "", "graphify failed")

            result = graph_loop.request_incremental_update(
                repo_root=ROOT,
                status_path=status_path,
                event="validated_stage_handoff",
                artifact_validated=True,
                runner=failing_runner,
            )

            self.assertEqual(result["state"], "stale")
            self.assertEqual(page_state.read_text(encoding="utf-8"), "canonical-state\n")
            self.assertIn('"state": "stale"', status_path.read_text(encoding="utf-8"))

    def test_dry_run_cli_does_not_build_graph(self):
        runtime = ROOT / "tests/factory/.runtime"
        runtime.mkdir(exist_ok=True)
        with workspace_tempdir(runtime) as tmp:
            status_path = tmp / "GRAPH_STATUS.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo-root",
                    str(ROOT),
                    "--status",
                    str(status_path),
                    "--event",
                    "validated_stage_handoff",
                    "--artifact-validated",
                    "--dry-run",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("PASS: incremental graph update eligible", result.stdout)
            self.assertFalse(status_path.exists())


    def test_status_and_update_command_use_project_configuration(self):
        graph_loop = load_graph_loop()
        runtime = ROOT / "tests/factory/.runtime"
        with workspace_tempdir(runtime) as tmp:
            (tmp / ".site-factory").mkdir()
            (tmp / ".site-factory/project.json").write_text(
                json.dumps(
                    {
                        "project_id": "configured-site",
                        "paths": {"graph_profile": "graph/CUSTOM_PROFILE.json"},
                    }
                ),
                encoding="utf-8",
            )
            status_path = tmp / "GRAPH_STATUS.json"
            captured = {}

            def successful_runner(command, **kwargs):
                captured["command"] = command
                return subprocess.CompletedProcess(command, 0, "", "")

            result = graph_loop.request_incremental_update(
                repo_root=tmp,
                status_path=status_path,
                event="validated_stage_handoff",
                artifact_validated=True,
                runner=successful_runner,
            )

            self.assertEqual(result["project_id"], "configured-site")
            profile_index = captured["command"].index("--profile") + 1
            self.assertEqual(captured["command"][profile_index], "graph/CUSTOM_PROFILE.json")


if __name__ == "__main__":
    unittest.main()
