import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

from tests.factory.workspace_tempdir import workspace_tempdir


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / ".agents/skills/loop-engine/scripts/state_engine.py"


def load_state_engine():
    spec = importlib.util.spec_from_file_location("state_engine", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load state engine from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class StateEngineTests(unittest.TestCase):
    def test_normal_transition(self):
        engine = load_state_engine()

        self.assertEqual(
            engine.validate_transition("queued", "contract_ready", None),
            [],
        )

    def test_creative_requires_creative_approval(self):
        engine = load_state_engine()

        errors = engine.validate_transition(
            "contract_ready",
            "creative_approved",
            None,
        )

        self.assertTrue(any("creative approval" in error.lower() for error in errors))

    def test_creative_approval_allows_transition(self):
        engine = load_state_engine()

        errors = engine.validate_transition(
            "contract_ready",
            "creative_approved",
            {"scope": "creative", "state": "approved"},
        )

        self.assertEqual(errors, [])

    def test_production_requires_production_approval(self):
        engine = load_state_engine()

        errors = engine.validate_transition(
            "staging_ready",
            "released",
            {"scope": "creative", "state": "approved"},
        )

        self.assertTrue(any("production approval" in error.lower() for error in errors))

    def test_assets_ready_and_not_needed_both_route_to_built(self):
        engine = load_state_engine()

        self.assertEqual(engine.validate_transition("assets_ready", "built", None), [])
        self.assertEqual(
            engine.validate_transition("assets_not_needed", "built", None),
            [],
        )

    def test_blocker_does_not_replace_lifecycle(self):
        engine = load_state_engine()

        state = engine.PageState(
            page_id="page-home",
            route="/",
            priority="P0",
            status="built",
            stage="06-integrated-qa-refinement",
            blocker="build failed",
        )

        self.assertEqual(state.status, "built")
        self.assertEqual(state.blocker, "build failed")

    def test_growth_keeps_iteration_stage_separate(self):
        engine = load_state_engine()

        state = engine.PageState(
            page_id="page-home",
            route="/",
            priority="P0",
            status="growth",
            stage="07-release-growth",
            iteration_stage="02-creative-blueprint",
        )

        self.assertEqual(state.status, "growth")
        self.assertEqual(state.iteration_stage, "02-creative-blueprint")

    def test_parse_page_queue_fixture(self):
        engine = load_state_engine()
        fixture = ROOT / "tests/factory/fixtures/page-queue-valid.md"

        pages = engine.parse_page_queue(fixture.read_text(encoding="utf-8"))

        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0].page_id, "page-home")
        self.assertEqual(pages[0].status, "contract_ready")
        self.assertEqual(pages[0].stage, "02-creative-blueprint")

    def test_parse_next_task_fixture(self):
        engine = load_state_engine()
        fixture = ROOT / "tests/factory/fixtures/next-task-valid.md"

        task = engine.parse_next_task(fixture.read_text(encoding="utf-8"))

        self.assertEqual(task.page, "page-home")
        self.assertEqual(task.approval, "creative_pending")
        self.assertEqual(task.inputs, ["docs/pages/home/PAGE_CONTRACT.md"])

    def test_status_is_russian(self):
        engine = load_state_engine()
        page = engine.PageState(
            page_id="page-home",
            route="/",
            priority="P0",
            status="contract_ready",
            stage="02-creative-blueprint",
        )
        task = engine.NextTask(
            page="page-home",
            stage="02-creative-blueprint",
            owner="webpage-factory/02-creative-blueprint",
            approval="creative_pending",
            inputs=["docs/pages/home/PAGE_CONTRACT.md"],
            output="docs/pages/home/CREATIVE_BLUEPRINT.md",
        )

        rendered = engine.render_status_ru([page], task)

        self.assertIn("Панель владельца", rendered)
        self.assertIn("Контракт готов", rendered)
        self.assertIn("Требуется согласование", rendered)

    def test_atomic_write_replaces_complete_file(self):
        engine = load_state_engine()
        runtime = ROOT / "tests/factory/.runtime"
        runtime.mkdir(exist_ok=True)
        with workspace_tempdir(runtime) as tmp:
            target = tmp / "STATUS.md"
            target.write_text("старое", encoding="utf-8")

            engine.atomic_write(target, "новое\n")

            self.assertEqual(target.read_text(encoding="utf-8"), "новое\n")

    def test_generate_status_cli_writes_russian_dashboard(self):
        runtime = ROOT / "tests/factory/.runtime"
        runtime.mkdir(exist_ok=True)
        script = MODULE_PATH.with_name("generate_status.py")
        queue = ROOT / "tests/factory/fixtures/page-queue-valid.md"
        task = ROOT / "tests/factory/fixtures/next-task-valid.md"
        with workspace_tempdir(runtime) as tmp:
            output = tmp / "STATUS.md"

            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--queue",
                    str(queue),
                    "--task",
                    str(task),
                    "--output",
                    str(output),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            rendered = output.read_text(encoding="utf-8")
            self.assertIn("Панель владельца", rendered)
            self.assertIn("Креативное направление", rendered)

    def test_state_bundle_keeps_queue_task_status_and_log_consistent(self):
        engine = load_state_engine()
        runtime = ROOT / "tests/factory/.runtime"
        runtime.mkdir(exist_ok=True)
        page = engine.PageState(
            page_id="page-home",
            route="/",
            priority="P0",
            status="queued",
            stage="01-page-contract",
        )
        task = engine.select_next_task([page]).task
        with workspace_tempdir(runtime) as tmp:
            queue = tmp / "PAGE_QUEUE.md"
            next_task = tmp / "NEXT_TASK.md"
            status = tmp / "STATUS.md"
            log = tmp / "LOOP_LOG.md"

            engine.write_state_bundle(
                queue,
                next_task,
                status,
                log,
                [page],
                task,
                "## 2026-07-13 — dry state update\n- Результат: готово",
            )

            self.assertEqual(engine.parse_page_queue(queue.read_text(encoding="utf-8"))[0], page)
            self.assertEqual(engine.parse_next_task(next_task.read_text(encoding="utf-8")), task)
            self.assertIn("Панель владельца", status.read_text(encoding="utf-8"))
            self.assertIn("dry state update", log.read_text(encoding="utf-8"))


    def test_contract_task_uses_configured_source_paths(self):
        engine = load_state_engine()
        page = engine.PageState(
            page_id="page-home",
            route="/",
            priority="P0",
            status="queued",
            stage="01-page-contract",
        )

        task = engine.select_next_task(
            [page],
            configured_paths={
                "page_queue": "planning/PAGES.md",
                "master_context": "context/MASTER.md",
            },
        ).task

        self.assertEqual(task.inputs, ["planning/PAGES.md", "context/MASTER.md"])


if __name__ == "__main__":
    unittest.main()
