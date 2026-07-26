from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / ".agents/skills/loop-engine/scripts"))

from state_engine import validate_transition


MODE_TRANSITIONS = {
    "staging_prepare": ("qa_passed", "staging_ready"),
    "production_release": ("staging_ready", "released"),
    "growth_iteration": ("released", "growth"),
}

ITERATION_STAGES = {
    "01-page-contract",
    "02-creative-blueprint",
    "03-conversion-copy",
    "04-page-assets",
    "05-full-page-build",
    "06-integrated-qa-refinement",
}

SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
ROLLBACK_FIELDS = {
    "page_id",
    "route",
    "release_id",
    "checkpoint",
    "restore_commands",
}
SECRET_PATTERN = re.compile(
    r"(?:token|password|passwd|secret|api[_-]?key|private[_-]?key)", re.IGNORECASE
)


def _parse_timestamp(value: object, field: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str):
        errors.append(f"production approval requires {field}")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"invalid production approval {field}")
        return None
    if parsed.tzinfo is None:
        errors.append(f"production approval {field} must include timezone")
        return None
    return parsed.astimezone(timezone.utc)


def _validate_approval(path: Path | None, args, errors: list[str]) -> dict | None:
    if path is None or not path.is_file():
        errors.append("production approval file is required")
        return None
    try:
        approval = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid production approval file: {exc}")
        return None
    expected = {
        "scope": "production",
        "state": "approved",
        "page_id": args.page_id,
        "route": args.route,
        "release_id": args.release_id,
    }
    for key, value in expected.items():
        if approval.get(key) != value:
            errors.append(f"production approval {key} does not match release scope")
    approved_at = _parse_timestamp(approval.get("approved_at"), "approved_at", errors)
    expires_at = _parse_timestamp(approval.get("expires_at"), "expires_at", errors)
    now = datetime.now(timezone.utc)
    if approved_at is not None and approved_at > now + timedelta(minutes=5):
        errors.append("production approval approved_at is in the future")
    if expires_at is not None and expires_at <= now:
        errors.append("production approval has expired")
    if approved_at is not None and expires_at is not None and expires_at <= approved_at:
        errors.append("production approval expires_at must follow approved_at")
    return approval


def _validate_rollback(path: Path | None, args, errors: list[str]) -> None:
    if path is None or not path.is_file():
        errors.append("rollback evidence file is required")
        return
    try:
        rollback = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid rollback evidence file: {exc}")
        return
    if not isinstance(rollback, dict):
        errors.append("rollback evidence must be a JSON object")
        return

    unexpected = set(rollback) - ROLLBACK_FIELDS
    if unexpected:
        errors.append(
            "rollback evidence has unsupported fields: " + ", ".join(sorted(unexpected))
        )
    expected = {
        "page_id": args.page_id,
        "route": args.route,
        "release_id": args.release_id,
    }
    for key, value in expected.items():
        if rollback.get(key) != value:
            errors.append(f"rollback evidence {key} does not match release scope")

    checkpoint = rollback.get("checkpoint")
    if not isinstance(checkpoint, str) or not checkpoint.strip():
        errors.append("rollback evidence requires a checkpoint")
    commands = rollback.get("restore_commands")
    if (
        not isinstance(commands, list)
        or not commands
        or any(not isinstance(command, str) or not command.strip() for command in commands)
    ):
        errors.append("rollback evidence requires non-empty restore_commands")

    serialized = json.dumps(rollback, ensure_ascii=False)
    if SECRET_PATTERN.search(serialized):
        errors.append("rollback evidence must not contain secrets")


def _validate_history(args, errors: list[str]) -> None:
    if args.history_file is None:
        errors.append("canonical release history file is required")
        return
    expected_history = (args.repo_root / "docs/system/LOOP_LOG.md").resolve()
    if args.history_file.resolve() != expected_history:
        errors.append("release history must use canonical docs/system/LOOP_LOG.md")
        return
    if args.previous_history_size is None or args.previous_history_sha256 is None:
        errors.append("previous release history size and sha256 are required")
        return
    if not SHA256_PATTERN.fullmatch(args.previous_history_sha256):
        errors.append("previous release history sha256 must use sha256:<64 lowercase hex>")
        return
    try:
        current = args.history_file.read_bytes()
    except OSError as exc:
        errors.append(f"release history cannot be read: {exc}")
        return
    if args.previous_history_size < 0 or args.previous_history_size >= len(current):
        errors.append("release history must contain a non-empty appended transition")
        return
    previous = current[: args.previous_history_size]
    actual_hash = "sha256:" + hashlib.sha256(previous).hexdigest()
    if actual_hash != args.previous_history_sha256:
        errors.append("release history previous prefix hash does not match")
        return
    try:
        appended = current[args.previous_history_size :].decode("utf-8")
    except UnicodeDecodeError:
        errors.append("release history append must be valid UTF-8")
        return
    raw_lines = {line.strip() for line in appended.splitlines() if line.strip()}
    record_lines = {
        line[2:].strip() if line.startswith("- ") else line for line in raw_lines
    }
    scope_markers = {
        f"## {args.mode} {args.release_id}",
        f"page_id: {args.page_id}",
        f"route: {args.route}",
        f"transition: {args.from_status} -> {args.to_status}",
    }
    if args.mode == "growth_iteration":
        scope_markers.add(f"iteration_stage: {args.iteration_stage}")
    if not scope_markers.issubset(record_lines):
        errors.append("release history append does not match full transition scope")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a mode-aware Stage 7 release or growth transition."
    )
    parser.add_argument("--mode", choices=sorted(MODE_TRANSITIONS), required=True)
    parser.add_argument("--from-status", required=True)
    parser.add_argument("--to-status", required=True)
    parser.add_argument("--page-id", required=True)
    parser.add_argument("--route", required=True)
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--approval-file", type=Path)
    parser.add_argument("--rollback", type=Path)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--history-file", type=Path)
    parser.add_argument("--previous-history-size", type=int)
    parser.add_argument("--previous-history-sha256")
    parser.add_argument("--iteration-stage")
    args = parser.parse_args()

    errors = []
    expected_transition = MODE_TRANSITIONS[args.mode]
    if (args.from_status, args.to_status) != expected_transition:
        errors.append(
            f"mode {args.mode} requires {expected_transition[0]} -> {expected_transition[1]}"
        )

    approval = None
    if args.mode == "production_release":
        approval = _validate_approval(args.approval_file, args, errors)
    transition_approval = None
    if approval is not None:
        transition_approval = {
            "scope": approval.get("scope"),
            "state": approval.get("state"),
        }
    errors.extend(
        validate_transition(args.from_status, args.to_status, transition_approval)
    )

    if args.mode in {"staging_prepare", "production_release"}:
        _validate_rollback(args.rollback, args, errors)

    if args.mode in {"production_release", "growth_iteration"}:
        _validate_history(args, errors)

    if args.mode == "growth_iteration" and args.iteration_stage not in ITERATION_STAGES:
        errors.append("growth_iteration requires a valid iteration_stage")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(
        f"PASS: {args.mode} {args.page_id} {args.route} "
        f"{args.from_status} -> {args.to_status} ({args.release_id})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
