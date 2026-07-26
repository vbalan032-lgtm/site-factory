from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
from typing import Iterable, Mapping


class SnapshotError(ValueError):
    pass


GENERATED_PARTS = {"__pycache__"}
GENERATED_SUFFIXES = {".pyc", ".pyo"}


def _relative_path(value: str) -> Path:
    normalized = value.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if pure.is_absolute() or ".." in pure.parts or ":" in normalized:
        raise SnapshotError("owned paths must be repository-relative")
    return Path(*pure.parts)


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _is_generated(path: Path) -> bool:
    return bool(GENERATED_PARTS.intersection(path.parts)) or path.suffix in GENERATED_SUFFIXES


def build_manifest(repo_root: Path, owned_paths: Iterable[str]) -> dict[str, str]:
    manifest: dict[str, str] = {}
    for value in owned_paths:
        relative = _relative_path(value)
        target = repo_root / relative
        if target.is_file():
            manifest[relative.as_posix()] = _digest(target)
        elif target.is_dir():
            for path in sorted(
                item for item in target.rglob("*")
                if item.is_file() and not _is_generated(item.relative_to(repo_root))
            ):
                manifest[path.relative_to(repo_root).as_posix()] = _digest(path)
    return manifest


def detect_drift(repo_root: Path, installed_files: Mapping[str, str]) -> tuple[str, ...]:
    drift: list[str] = []
    for value, expected in installed_files.items():
        relative = _relative_path(value)
        path = repo_root / relative
        if not path.is_file() or _digest(path) != expected:
            drift.append(relative.as_posix())
    return tuple(sorted(drift))

