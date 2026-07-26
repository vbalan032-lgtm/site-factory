import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / ".agents/skills/loop-engine/scripts"
STATE_ENGINE = SCRIPTS / "state_engine.py"
DRY_RUNNER = SCRIPTS / "run_dry_scenarios.py"


def load_state_engine():
    spec = importlib.util.spec_from_file_location("loop_state_engine", STATE_ENGINE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load state engine from {STATE_ENGINE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class DryScenarioTests(unittest.TestCase):
    def test_exact_lifecycle_stage_mapping(self):
        engine = load_state_engine()
        expected = {
            "queued": "01-page-contract",
            "contract_ready": "02-creative-blueprint",
            "creative_approved": "03-conversion-copy",
            "copy_ready": "04-page-assets",
            "assets_ready": "05-full-page-build",
            "assets_not_needed": "05-full-page-build",
            "built": "06-integrated-qa-refinement",
            "qa_passed": "07-release-growth",
            "staging_ready": "07-release-growth",
            "released": "07-release-growth",
            "growth": "07-release-growth",
        }
        self.assertEqual(engine.STAGE_BY_STATUS, expected)

    def test_failed_build_and_ci_preempt_page_work(self):
        engine = load_state_engine()
        page = engine.PageState("page-home", "/", "P0", "contract_ready", "02-creative-blueprint")

        for signals in (
            engine.LoopSignals(failed_build=True),
            engine.LoopSignals(failed_ci=True),
        ):
            selected = engine.select_next_task([page], signals)
            self.assertEqual(selected.task.stage, "repair")
            self.assertEqual(selected.task.owner, "loop-engine/loop-failed-build-repair")

    def test_graph_fallback_preserves_selected_page_stage(self):
        engine = load_state_engine()
        page = engine.PageState("page-home", "/", "P0", "contract_ready", "02-creative-blueprint")

        for graph_state in ("stale", "unavailable"):
            selected = engine.select_next_task(
                [page], engine.LoopSignals(graph_state=graph_state)
            )
            self.assertEqual(selected.task.stage, "02-creative-blueprint")
            self.assertTrue(any("filesystem fallback" in item for item in selected.warnings))

    def test_changed_fingerprint_and_disputed_claim_require_exact_sources(self):
        engine = load_state_engine()
        page = engine.PageState("page-home", "/", "P0", "contract_ready", "02-creative-blueprint")
        selected = engine.select_next_task(
            [page],
            engine.LoopSignals(changed_fingerprint=True, disputed_claim=True),
        )

        self.assertEqual(selected.task.stage, "02-creative-blueprint")
        self.assertTrue(any("fingerprint" in item for item in selected.warnings))
        self.assertTrue(any("claim" in item for item in selected.warnings))

    def test_state_transition_requires_valid_artifact_before_mutation(self):
        engine = load_state_engine()
        page = engine.PageState("page-home", "/", "P0", "queued", "01-page-contract")

        with self.assertRaises(engine.StateValidationError):
            engine.transition_page(
                [page],
                "page-home",
                "contract_ready",
                artifact_errors=["source fingerprint mismatch"],
            )

        self.assertEqual(page.status, "queued")

    def test_next_task_renderer_has_only_canonical_fields(self):
        engine = load_state_engine()
        page = engine.PageState("page-home", "/", "P0", "queued", "01-page-contract")
        task = engine.select_next_task([page]).task

        rendered = engine.render_next_task(task)

        keys = {
            line[2:].split(":", 1)[0]
            for line in rendered.splitlines()
            if line.startswith("- ")
        }
        self.assertEqual(keys, {"page", "stage", "owner", "approval", "inputs", "output"})

    def test_dry_runner_covers_every_approved_scenario(self):
        result = subprocess.run(
            [sys.executable, str(DRY_RUNNER), "--repo-root", str(ROOT)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        expected = {
            "new_page",
            "homepage_continuation",
            "changed_source_fingerprint",
            "disputed_claim",
            "assets_required",
            "assets_not_needed",
            "build_failure",
            "creative_approval_pending",
            "creative_approval_approved",
            "production_approval_missing",
            "production_approval_granted",
            "graph_current",
            "graph_stale",
            "graph_unavailable",
        }
        passed = {
            line.removeprefix("PASS: ").strip()
            for line in result.stdout.splitlines()
            if line.startswith("PASS: ")
        }
        self.assertEqual(passed, expected)


if __name__ == "__main__":
    unittest.main()
