from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from typing import Callable


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from state_engine import atomic_write


VALIDATED_EVENT = "validated_stage_handoff"


def should_update(event: str, artifact_validated: bool) -> bool:
    return event == VALIDATED_EVENT and artifact_validated


def _project_settings(repo_root: Path) -> tuple[str, str]:
    config_path = repo_root / ".site-factory/project.json"
    if not config_path.is_file():
        return "unconfigured-project", "docs/system/knowledge-graph/GRAPH_PROFILE.json"
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        project_id = data.get("project_id", "unconfigured-project")
        graph_profile = data.get("paths", {}).get(
            "graph_profile", "docs/system/knowledge-graph/GRAPH_PROFILE.json"
        )
    except (OSError, json.JSONDecodeError, AttributeError):
        return "unconfigured-project", "docs/system/knowledge-graph/GRAPH_PROFILE.json"
    return str(project_id), str(graph_profile)


def _status_payload(
    state: str, event: str, reason: str, project_id: str = "unconfigured-project"
) -> dict[str, str]:
    return {
        "schema_version": "1.0",
        "project_id": project_id,
        "state": state,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source_event": event,
        "reason": reason,
    }


def _write_status(path: Path, payload: dict[str, str]) -> None:
    atomic_write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def request_incremental_update(
    repo_root: Path,
    status_path: Path,
    event: str,
    artifact_validated: bool,
    runner: Callable = subprocess.run,
) -> dict[str, str]:
    repo_root = repo_root.resolve()
    project_id, graph_profile = _project_settings(repo_root)
    if not should_update(event, artifact_validated):
        payload = _status_payload(
            "unavailable",
            event,
            "incremental update skipped: no validated stage handoff",
            project_id,
        )
        _write_status(status_path, payload)
        return payload

    update_script = (
        repo_root
        / ".agents/skills/shared/knowledge-graph-router/scripts/update_graph.py"
    )
    command = [
        sys.executable,
        str(update_script),
        "--profile",
        graph_profile,
        "--repo-root",
        str(repo_root),
        "--incremental",
        "--directed",
        "--no-viz",
        "--status",
        str(status_path),
    ]
    result = runner(
        command,
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode == 0:
        payload = _status_payload(
            "current", event, "incremental update completed", project_id
        )
    else:
        detail = (result.stderr or result.stdout or "graph update failed").strip()
        payload = _status_payload("stale", event, detail[:500], project_id)
    _write_status(status_path, payload)
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Request one bounded knowledge-graph update after a validated stage."
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--status",
        type=Path,
        default=Path("docs/system/knowledge-graph/GRAPH_STATUS.json"),
    )
    parser.add_argument("--event", required=True)
    parser.add_argument("--artifact-validated", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.dry_run:
        if should_update(args.event, args.artifact_validated):
            print("PASS: incremental graph update eligible")
            return 0
        print("PASS: graph update skipped for non-handoff event")
        return 0

    repo_root = args.repo_root.resolve()
    status_path = args.status
    if not status_path.is_absolute():
        status_path = repo_root / status_path
    result = request_incremental_update(
        repo_root,
        status_path,
        args.event,
        args.artifact_validated,
    )
    print(f"PASS: graph state is {result['state']}")
    return 0 if result["state"] != "stale" else 1


if __name__ == "__main__":
    raise SystemExit(main())
