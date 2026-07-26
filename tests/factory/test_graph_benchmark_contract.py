import importlib.util
import json
import sys
import unittest
from pathlib import Path

from tests.factory.workspace_tempdir import workspace_tempdir


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / ".agents/skills/shared/knowledge-graph-router/scripts/benchmark_context.py"


def load_module():
    spec = importlib.util.spec_from_file_location("benchmark_contract_under_test", MODULE)
    if spec is None or spec.loader is None:
        raise RuntimeError("benchmark_context.py is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class GraphBenchmarkContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_v11_cases_are_a_two_route_seven_stage_matrix(self):
        runtime = ROOT / "tests/factory/.runtime"
        cases = [
            {
                "id": f"{route}:{stage}",
                "route": route,
                "stage": stage,
                "question": "context",
                "filesystem_allowlist": ["source.md"],
                "required_facts": ["fact"],
                "required_exact_locators": [],
            }
            for route in ("/", "/product/")
            for stage in self.module.FACTORY_STAGES
        ]
        with workspace_tempdir(runtime) as tmp:
            path = tmp / "cases.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": "1.1",
                        "project_id": "fixture",
                        "cases": cases,
                    }
                ),
                encoding="utf-8",
            )
            loaded = self.module._load_cases(path, "fixture")

        self.assertEqual(len(loaded), 14)
        self.assertEqual(
            {(case["route"], case["stage"]) for case in loaded},
            {
                (route, stage)
                for route in ("/", "/product/")
                for stage in self.module.FACTORY_STAGES
            },
        )

    def test_case_gates_require_facts_exact_slices_no_full_files_and_budget(self):
        verdict = self.module.evaluate_case_gates(
            required_facts=["Product-X", "reviewed workflow"],
            required_exact_locators=["heading:Claims > Approved"],
            evidence_text="Product-X uses reviewed workflow.",
            exact_locators={"heading:Claims > Approved"},
            loaded_files=(),
            excluded_reasons=("summary_budget_exceeded",),
            total_tokens=120,
            total_limit=200,
        )
        self.assertTrue(verdict["passed"])
        self.assertEqual(verdict["required_fact_coverage_percent"], 100.0)
        self.assertEqual(verdict["exact_slice_coverage_percent"], 100.0)

        failed = self.module.evaluate_case_gates(
            required_facts=["Product-X", "missing"],
            required_exact_locators=["heading:Claims > Approved"],
            evidence_text="Product-X",
            exact_locators=set(),
            loaded_files=("claims.md",),
            excluded_reasons=("changed_source",),
            total_tokens=220,
            total_limit=200,
        )
        self.assertFalse(failed["passed"])
        self.assertEqual(failed["required_fact_coverage_percent"], 50.0)
        self.assertIn("changed_source", failed["disallowed_exclusions"])


if __name__ == "__main__":
    unittest.main()
