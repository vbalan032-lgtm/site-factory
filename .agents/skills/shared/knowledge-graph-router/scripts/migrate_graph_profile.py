from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path, PurePosixPath
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from graph_profile import FACTORY_STAGES  # noqa: E402
from source_resolver import (  # noqa: E402
    locator_from_legacy_location,
    resolve_source_slice,
)


DEFAULT_STAGE_TOTALS = {
    "01-page-contract": 1800,
    "02-creative-blueprint": 1800,
    "03-conversion-copy": 1600,
    "04-page-assets": 1000,
    "05-full-page-build": 1400,
    "06-integrated-qa-refinement": 1800,
    "07-release-growth": 900,
}


def _rule_for_path(profile: dict[str, object], source_path: str) -> dict[str, object]:
    path_parts = PurePosixPath(source_path.replace("\\", "/")).parts
    matches: list[tuple[int, dict[str, object]]] = []
    for raw_rule in profile.get("corpus_rules", []):
        if not isinstance(raw_rule, dict):
            continue
        root = raw_rule.get("root")
        if not isinstance(root, str):
            continue
        root_parts = PurePosixPath(root).parts
        if path_parts[: len(root_parts)] == root_parts:
            matches.append((len(root_parts), raw_rule))
    if not matches:
        raise ValueError(f"source path has no corpus rule: {source_path}")
    return max(matches, key=lambda item: item[0])[1]


def migrate_profile_data(data: dict[str, object]) -> dict[str, object]:
    migrated = copy.deepcopy(data)
    version = migrated.get("schema_version")
    if version not in {"1.0", "1.1"}:
        raise ValueError(f"unsupported graph profile schema_version: {version}")

    roots = migrated.get("corpus_roots")
    if not isinstance(roots, list) or not roots:
        raise ValueError("corpus_roots must be a non-empty list")
    if version == "1.0":
        migrated["corpus_rules"] = [
            {
                "root": root,
                "source_role": "canonical",
                "stages": list(FACTORY_STAGES),
                "index_mode": "sections",
            }
            for root in roots
        ]

    budgets = migrated.get("stage_budgets")
    if not isinstance(budgets, dict):
        raise ValueError("stage_budgets must be an object")
    split: dict[str, dict[str, int]] = {}
    for stage in FACTORY_STAGES:
        budget = budgets.get(stage, DEFAULT_STAGE_TOTALS[stage])
        if isinstance(budget, dict):
            split[stage] = copy.deepcopy(budget)
            continue
        if not isinstance(budget, int) or isinstance(budget, bool) or budget <= 0:
            raise ValueError(f"missing positive budget for stage: {stage}")
        summary = max(1, budget * 3 // 5)
        split[stage] = {
            "summary_tokens": summary,
            "exact_tokens": max(1, budget - summary),
            "total_tokens": budget,
            "top_k": 12,
        }
    migrated["stage_budgets"] = split
    migrated["schema_version"] = "1.1"
    return migrated


def migrate_seed_data(
    repo_root: Path,
    data: dict[str, object],
    profile: dict[str, object],
) -> dict[str, object]:
    migrated = copy.deepcopy(data)
    version = migrated.get("schema_version")
    if version not in {"1.0", "1.1"}:
        raise ValueError(f"unsupported knowledge seed schema_version: {version}")
    nodes = migrated.get("nodes")
    if not isinstance(nodes, list):
        raise ValueError("knowledge seed nodes must be a list")

    for raw_node in nodes:
        if not isinstance(raw_node, dict):
            raise ValueError("knowledge seed node must be an object")
        source_path = raw_node.get("source_path")
        if not isinstance(source_path, str) or not source_path.strip():
            raise ValueError("knowledge seed node source_path is required")
        absolute = repo_root / Path(*PurePosixPath(source_path).parts)
        locator = raw_node.get("source_locator")
        if not isinstance(locator, str) or not locator.strip():
            location = raw_node.get("source_location")
            if not isinstance(location, str) or not location.strip():
                raise ValueError("knowledge seed node requires a source locator")
            locator = locator_from_legacy_location(absolute, location)
        resolve_source_slice(absolute, locator)
        rule = _rule_for_path(profile, source_path)
        raw_node["source_locator"] = locator
        raw_node.setdefault("source_role", rule["source_role"])
        raw_node.setdefault("lifecycle_state", "current")

    migrated["schema_version"] = "1.1"
    return migrated


def _write_json(path: Path, data: dict[str, object]) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Migrate a graph profile and curated seed from schema 1.0 to 1.1."
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--seed", required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    profile_path = (repo_root / args.profile).resolve()
    seed_path = (repo_root / args.seed).resolve()
    profile = migrate_profile_data(json.loads(profile_path.read_text(encoding="utf-8")))
    seed = migrate_seed_data(
        repo_root,
        json.loads(seed_path.read_text(encoding="utf-8")),
        profile,
    )
    result = {
        "profile": profile_path.relative_to(repo_root).as_posix(),
        "seed": seed_path.relative_to(repo_root).as_posix(),
        "schema_version": "1.1",
        "nodes": len(seed.get("nodes", [])),
        "written": bool(args.write),
    }
    if args.write:
        _write_json(profile_path, profile)
        _write_json(seed_path, seed)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
