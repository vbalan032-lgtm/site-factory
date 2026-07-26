from __future__ import annotations

import argparse
from pathlib import Path

from artifact_contracts import (
    ARTIFACT_FILENAMES,
    parse_frontmatter,
    source_fingerprint,
    validate_completed_artifact,
)


InputRequirement = tuple[str, tuple[str, ...]]


def _decision_value(decisions: list, decision_id: str):
    for decision in decisions:
        if isinstance(decision, dict) and decision.get("id") == decision_id:
            return decision.get("value")
    return None


def _validate_previous_input(
    artifact_data: dict,
    input_path: Path,
    kind: str,
    statuses: tuple[str, ...],
    repo_root: Path,
) -> list[str]:
    errors = validate_completed_artifact(input_path, kind, repo_root, set(statuses))
    if errors:
        return [f"{ARTIFACT_FILENAMES[kind]}: {error}" for error in errors]

    input_data, _ = parse_frontmatter(input_path.read_text(encoding="utf-8"))
    if input_data["page_id"] != artifact_data["page_id"]:
        errors.append(f"{ARTIFACT_FILENAMES[kind]} page_id does not match")
    if input_data["route"] != artifact_data["route"]:
        errors.append(f"{ARTIFACT_FILENAMES[kind]} route does not match")

    root = repo_root.resolve()
    try:
        relative = input_path.resolve().relative_to(root).as_posix()
    except ValueError:
        errors.append(f"{ARTIFACT_FILENAMES[kind]} escapes repository root")
        return errors
    expected = source_fingerprint(
        input_path.resolve(), root, str(artifact_data["schema_version"])
    )
    recorded = artifact_data["source_fingerprints"].get(relative)
    if recorded != expected:
        errors.append(
            f"handoff fingerprint missing or stale for {ARTIFACT_FILENAMES[kind]}"
        )
    return errors


def run_artifact_stage(
    artifact_kind: str,
    stage_name: str,
    completion_statuses: tuple[str, ...],
    required_inputs: tuple[InputRequirement, ...] = (),
    argv: list[str] | None = None,
    allow_not_needed: bool = False,
    not_needed_inputs: tuple[InputRequirement, ...] = (),
    asset_gate: bool = False,
) -> int:
    parser = argparse.ArgumentParser(
        description=f"Validate the completed output and handoff of project {stage_name}."
    )
    parser.add_argument("artifact", type=Path, nargs="?")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--input",
        action="append",
        type=Path,
        default=[],
        help="Previous-stage artifact path; repeat for every required input.",
    )
    if allow_not_needed:
        parser.add_argument(
            "--not-needed",
            action="store_true",
            help="Validate PAGE_COPY.md completed with status assets_not_needed.",
        )
    args = parser.parse_args(argv)

    if args.artifact is None:
        parser.error("artifact path is required")

    not_needed = allow_not_needed and args.not_needed
    selected_kind = "PAGE_COPY" if not_needed else artifact_kind
    selected_statuses = ("assets_not_needed",) if not_needed else completion_statuses
    selected_requirements = not_needed_inputs if not_needed else required_inputs
    repo_root = args.repo_root.resolve()

    errors = validate_completed_artifact(
        args.artifact, selected_kind, repo_root, set(selected_statuses)
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    artifact_data, _ = parse_frontmatter(args.artifact.read_text(encoding="utf-8"))
    inputs_by_name = {path.name: path for path in args.input}
    for kind, statuses in selected_requirements:
        filename = ARTIFACT_FILENAMES[kind]
        input_path = inputs_by_name.get(filename)
        if input_path is None:
            errors.append(f"required previous-stage input is missing: {filename}")
            continue
        errors.extend(
            _validate_previous_input(
                artifact_data, input_path, kind, statuses, repo_root
            )
        )

    if not_needed and _decision_value(artifact_data["decisions"], "assets") != "not_needed":
        errors.append("assets_not_needed requires decision assets=not_needed")

    if asset_gate:
        page_copy = inputs_by_name.get(ARTIFACT_FILENAMES["PAGE_COPY"])
        if page_copy is not None:
            page_copy_data, _ = parse_frontmatter(page_copy.read_text(encoding="utf-8"))
            if page_copy_data.get("status") != "assets_not_needed":
                manifest = inputs_by_name.get(ARTIFACT_FILENAMES["ASSET_MANIFEST"])
                if manifest is None:
                    errors.append(
                        "ASSET_MANIFEST.md with assets_ready is required when assets are needed"
                    )
                else:
                    errors.extend(
                        _validate_previous_input(
                            artifact_data,
                            manifest,
                            "ASSET_MANIFEST",
                            ("assets_ready",),
                            repo_root,
                        )
                    )

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"PASS: {selected_kind} {args.artifact}")
    return 0
