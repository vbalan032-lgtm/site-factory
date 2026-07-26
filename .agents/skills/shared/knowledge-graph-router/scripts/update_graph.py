from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from graph_profile import load_graph_profile
from graphify_provider import GraphifyJsonProvider


def _write_status(
    path: Path,
    project_id: str,
    state: str,
    source_event: str,
    reason: str,
) -> None:
    payload = {
        "schema_version": "1.0",
        "project_id": project_id,
        "state": state,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source_event": source_event,
        "reason": reason,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a project graph profile and run one bounded Graphify update."
    )
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--incremental", action="store_true")
    mode.add_argument("--full", action="store_true")
    parser.add_argument("--directed", action="store_true")
    parser.add_argument("--no-viz", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--status",
        type=Path,
        default=Path("docs/system/knowledge-graph/GRAPH_STATUS.json"),
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    profile_path = args.profile
    if not profile_path.is_absolute():
        profile_path = repo_root / profile_path
    profile = load_graph_profile(profile_path, repo_root)
    provider = GraphifyJsonProvider(profile, repo_root)
    command = (
        f"graphify extract {repo_root / 'graphify-out/.corpus'} "
        f"--out {repo_root / 'graphify-out/.provider-run'} --no-cluster"
    )
    update_kind = "incremental-safe" if args.incremental else "full"
    print(
        f"PROFILE: {profile.project_id} ({profile.provider}, {profile.extraction_mode})"
    )
    print(f"PLAN: {update_kind} {command}")
    print(f"POLICY: directed={args.directed} no_viz={args.no_viz}")
    if args.dry_run:
        print("PASS: dry-run; graph was not changed")
        return 0

    health = provider.update(profile, repo_root, incremental=args.incremental)
    for warning in health.warnings:
        print(f"WARNING: {warning}")
    if not health.available:
        status_path = args.status if args.status.is_absolute() else repo_root / args.status
        status_path.resolve().relative_to(repo_root)
        _write_status(
            status_path,
            profile.project_id,
            "stale",
            "explicit_graph_rebuild",
            "; ".join(health.warnings) or "graph update unavailable",
        )
        return 1
    status_path = args.status if args.status.is_absolute() else repo_root / args.status
    status_path.resolve().relative_to(repo_root)
    _write_status(
        status_path,
        profile.project_id,
        "current" if health.fresh else "stale",
        "explicit_graph_rebuild",
        (
            f"Graphify {profile.extraction_mode} graph: "
            f"nodes={health.node_count}, edges={health.edge_count}, "
            f"fresh={str(health.fresh).lower()}, stale_sources={len(health.stale_sources)}"
        ),
    )
    print(
        f"PASS: graph available={health.available} fresh={health.fresh} "
        f"nodes={health.node_count} edges={health.edge_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
