from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys
from uuid import uuid4


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from state_engine import (
    LoopSignals,
    PageState,
    StateValidationError,
    select_next_task,
    transition_page,
    validate_transition,
)


def _load_contract_runtime(repo_root: Path):
    scripts = repo_root / ".agents/skills/shared/factory-contracts/scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    from artifact_contracts import source_fingerprint, validate_completed_artifact

    return source_fingerprint, validate_completed_artifact


def _contract_fixture(repo_root: Path, runtime: Path) -> tuple[Path, Path, object]:
    source_fingerprint, validate_completed_artifact = _load_contract_runtime(repo_root)
    source = runtime / "source.md"
    source.write_text("Проверенный источник project.\n", encoding="utf-8")
    fingerprint = source_fingerprint(source, runtime, "1.0")
    contract = runtime / "PAGE_CONTRACT.md"
    contract.write_text(
        "---\n"
        'schema_version: "1.0"\n'
        "page_id: page-home\n"
        "route: /\n"
        "stage: stage-01-page-contract\n"
        "status: contract_ready\n"
        f"source_fingerprints: {json.dumps({'source.md': fingerprint})}\n"
        'decisions: [{"id":"language","value":"ru-Cyrl"}]\n'
        "unresolved_items: []\n"
        'approval: {"required":false,"state":"not_required","scope":"contract"}\n'
        'next_stage_inputs: ["PAGE_CONTRACT.md"]\n'
        "---\n\n"
        "# Контракт главной страницы\n\n"
        "project — компания отраслевых AI-экспертов для целевой отрасли.\n",
        encoding="utf-8",
    )
    return source, contract, validate_completed_artifact


def run_scenarios(repo_root: Path) -> list[tuple[str, bool, str]]:
    scratch_root = repo_root / ".tmp/loop-dry-run"
    scratch_root.mkdir(parents=True, exist_ok=True)
    runtime = scratch_root / f"run-{uuid4().hex}"
    runtime.mkdir()
    results: list[tuple[str, bool, str]] = []

    def check(name: str, condition: bool, detail: str = "") -> None:
        results.append((name, bool(condition), detail))

    try:
        source, contract, validate_completed_artifact = _contract_fixture(
            repo_root, runtime
        )
        queued = PageState(
            "page-new", "/new/", "P1", "queued", "01-page-contract"
        )
        check(
            "new_page",
            select_next_task([queued]).task.stage == "01-page-contract",
        )

        home = PageState(
            "page-home", "/", "P0", "queued", "01-page-contract"
        )
        contract_errors = validate_completed_artifact(
            contract, "PAGE_CONTRACT", runtime, {"contract_ready"}
        )
        transitioned = transition_page(
            [home], "page-home", "contract_ready", artifact_errors=contract_errors
        )
        check(
            "homepage_continuation",
            transitioned[0].status == "contract_ready"
            and select_next_task(transitioned).task.stage == "02-creative-blueprint",
            "; ".join(contract_errors),
        )

        source.write_text("Источник изменён.\n", encoding="utf-8")
        stale_errors = validate_completed_artifact(
            contract, "PAGE_CONTRACT", runtime, {"contract_ready"}
        )
        check(
            "changed_source_fingerprint",
            any("fingerprint mismatch" in error for error in stale_errors),
            "; ".join(stale_errors),
        )

        selected = select_next_task(
            transitioned, LoopSignals(disputed_claim=True)
        )
        check(
            "disputed_claim",
            any("exact-file proof" in warning for warning in selected.warnings),
        )

        for name, status in (
            ("assets_required", "assets_ready"),
            ("assets_not_needed", "assets_not_needed"),
        ):
            page = PageState("page-home", "/", "P0", status, "05-full-page-build")
            check(name, select_next_task([page]).task.stage == "05-full-page-build")

        repair = select_next_task(
            transitioned, LoopSignals(failed_build=True)
        ).task
        check(
            "build_failure",
            repair.stage == "repair"
            and repair.owner == "loop-engine/loop-failed-build-repair",
        )

        check(
            "creative_approval_pending",
            bool(validate_transition("contract_ready", "creative_approved", None)),
        )
        check(
            "creative_approval_approved",
            not validate_transition(
                "contract_ready",
                "creative_approved",
                {"scope": "creative", "state": "approved"},
            ),
        )
        check(
            "production_approval_missing",
            bool(validate_transition("staging_ready", "released", None)),
        )
        check(
            "production_approval_granted",
            not validate_transition(
                "staging_ready",
                "released",
                {"scope": "production", "state": "approved"},
            ),
        )

        for state in ("current", "stale", "unavailable"):
            selected = select_next_task(
                transitioned, LoopSignals(graph_state=state)
            )
            fallback_ok = state == "current" or any(
                "filesystem fallback" in warning for warning in selected.warnings
            )
            check(
                f"graph_{state}",
                selected.task.stage == "02-creative-blueprint" and fallback_ok,
            )
    except (OSError, StateValidationError, ValueError) as exc:
        results.append(("runtime", False, str(exc)))
    finally:
        shutil.rmtree(runtime, ignore_errors=True)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Loop Engine v3 scenarios without changing repository state."
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    results = run_scenarios(args.repo_root.resolve())
    failed = False
    for name, passed, detail in results:
        if passed:
            print(f"PASS: {name}")
        else:
            failed = True
            suffix = f" — {detail}" if detail else ""
            print(f"FAIL: {name}{suffix}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
