from __future__ import annotations

import argparse
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SkillRecord:
    name: str
    description: str
    path: Path
    body: str


def _frontmatter(text: str, path: Path) -> tuple[dict[str, str], str]:
    normalized = text.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        raise ValueError(f"{path}: SKILL.md must start with frontmatter")
    closing = normalized.find("\n---\n", 4)
    if closing < 0:
        raise ValueError(f"{path}: frontmatter closing delimiter is missing")

    metadata = {}
    for line in normalized[4:closing].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition(":")
        if separator:
            metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata, normalized[closing + 5 :]


def scan_skills(root: Path) -> list[SkillRecord]:
    records = []
    for path in sorted(root.rglob("SKILL.md")):
        text = path.read_text(encoding="utf-8")
        metadata, body = _frontmatter(text, path)
        records.append(
            SkillRecord(
                name=metadata.get("name", ""),
                description=metadata.get("description", ""),
                path=path,
                body=body,
            )
        )
    return records


def _referenced_local_paths(record: SkillRecord) -> list[Path]:
    references = []
    for match in re.findall(r"`((?:scripts|references|agents)/[^`]+)`", record.body):
        if "<" in match or ">" in match:
            continue
        references.append(record.path.parent / Path(match))
    return references


def validate_skill_root(root: Path) -> list[str]:
    errors = []
    try:
        records = scan_skills(root)
    except (OSError, UnicodeError, ValueError) as exc:
        return [str(exc)]

    for record in records:
        if not record.name:
            errors.append(f"{record.path}: name is required")
        if not record.description:
            errors.append(f"{record.path}: description is required")
        for referenced in _referenced_local_paths(record):
            if not referenced.exists():
                errors.append(f"{record.path}: referenced path does not exist: {referenced}")

        combined = f"{record.description}\n{record.body}"
        if re.search(
            r"(?is)(normal production owner|active owner|route normal production)"
            r".{0,160}docs/system/skill-archive",
            combined,
        ):
            errors.append(f"{record.path}: normal routing must not target the archive")

    counts = Counter(record.name for record in records if record.name)
    for name, count in sorted(counts.items()):
        if count > 1:
            paths = ", ".join(str(record.path) for record in records if record.name == name)
            errors.append(f"duplicate skill name '{name}' ({count}): {paths}")

    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate active project project skill metadata and names."
    )
    parser.add_argument("root", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    errors = validate_skill_root(args.root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    count = len(scan_skills(args.root))
    print(f"PASS: {count} active skill names are unique")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
