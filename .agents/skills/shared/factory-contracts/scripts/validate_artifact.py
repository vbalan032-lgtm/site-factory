from __future__ import annotations

import argparse
from pathlib import Path

from artifact_contracts import ARTIFACT_RULES, validate_artifact


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate one project page artifact contract."
    )
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--kind", required=True, choices=sorted(ARTIFACT_RULES))
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    return parser


def main() -> int:
    args = build_parser().parse_args()
    errors = validate_artifact(args.artifact, args.kind, args.repo_root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"PASS: {args.kind} {args.artifact}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
