from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re


HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
PYTHON_SYMBOL = re.compile(
    r"^(?P<indent>\s*)(?:async\s+def|def|class)\s+{name}\b"
)
BRACED_SYMBOL = re.compile(
    r"^\s*(?:(?:export\s+)?(?:default\s+)?(?:async\s+)?function|"
    r"(?:export\s+)?(?:const|let|var|class))\s+{name}\b"
)


@dataclass(frozen=True)
class SourceSlice:
    source_locator: str
    source_span: tuple[int, int]
    text: str
    file_sha256: str
    slice_sha256: str


def _sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _heading_name(value: str) -> str:
    value = re.sub(r"^В§?\s*\d+(?:\.\d+)*\.?\s*", "", value.strip())
    return re.sub(r"\s+", " ", value).casefold()


def _slice_result(
    path: Path, locator: str, lines: list[str], start: int, end: int
) -> SourceSlice:
    text = "".join(lines[start:end])
    return SourceSlice(
        source_locator=locator,
        source_span=(start + 1, end),
        text=text,
        file_sha256=_sha256(path.read_bytes()),
        slice_sha256=_sha256(text.encode("utf-8")),
    )


def _resolve_heading(path: Path, locator: str, lines: list[str]) -> SourceSlice:
    requested = [
        _heading_name(part)
        for part in re.split(r"\s+>\s+", locator.removeprefix("heading:"))
        if part.strip()
    ]
    if not requested:
        raise ValueError(f"source locator is empty: {locator}")
    stack: list[tuple[int, str]] = []
    headings: list[tuple[int, int, tuple[str, ...]]] = []
    for index, line in enumerate(lines):
        match = HEADING.match(line.rstrip("\r\n"))
        if not match:
            continue
        level = len(match.group(1))
        name = _heading_name(match.group(2))
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, name))
        headings.append((index, level, tuple(item[1] for item in stack)))

    target: tuple[int, int, tuple[str, ...]] | None = None
    for heading in headings:
        if list(heading[2]) == requested:
            target = heading
            break
    if target is None:
        raise ValueError(f"source locator did not resolve: {locator}")
    start, level, _ = target
    end = len(lines)
    for index, other_level, _ in headings:
        if index > start and other_level <= level:
            end = index
            break
    return _slice_result(path, locator, lines, start, end)


def locator_from_legacy_location(path: Path, source_location: str) -> str:
    if not isinstance(source_location, str) or not source_location.strip():
        raise ValueError("legacy source locator is required")
    requested = [
        _heading_name(part.removeprefix("В§"))
        for part in re.split(r"\s+/\s+", source_location.strip())
        if part.strip()
    ]
    if not requested:
        raise ValueError("legacy source locator is empty")
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    stack: list[tuple[int, str, str]] = []
    candidates: list[tuple[int, tuple[str, ...], tuple[str, ...]]] = []
    for index, line in enumerate(lines):
        match = HEADING.match(line.rstrip("\r\n"))
        if not match:
            continue
        level = len(match.group(1))
        raw = match.group(2).strip()
        normalized = _heading_name(raw)
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, raw, normalized))
        candidates.append(
            (
                index,
                tuple(item[1] for item in stack),
                tuple(item[2] for item in stack),
            )
        )

    ranked: list[tuple[int, int, tuple[str, ...]]] = []
    for index, raw_path, normalized_path in candidates:
        matched = 0
        for expected, actual in zip(reversed(requested), reversed(normalized_path)):
            if expected == actual or expected in actual or actual in expected:
                matched += 1
            else:
                break
        if matched:
            ranked.append((matched, -index, raw_path))
    if not ranked:
        raise ValueError(f"legacy source locator did not resolve: {source_location}")
    matched, _, raw_path = max(ranked, key=lambda item: (item[0], item[1]))
    if matched < len(requested):
        raise ValueError(f"legacy source locator is ambiguous: {source_location}")
    locator = "heading:" + " > ".join(raw_path)
    resolve_source_slice(path, locator)
    return locator


def _resolve_python_symbol(
    path: Path, locator: str, symbol: str, lines: list[str]
) -> SourceSlice | None:
    pattern = re.compile(PYTHON_SYMBOL.pattern.format(name=re.escape(symbol)))
    for start, line in enumerate(lines):
        match = pattern.match(line)
        if not match:
            continue
        indent = len(match.group("indent").expandtabs(4))
        end = len(lines)
        for index in range(start + 1, len(lines)):
            stripped = lines[index].strip()
            if not stripped or stripped.startswith("#"):
                continue
            current_indent = len(lines[index]) - len(lines[index].lstrip(" \t"))
            if current_indent <= indent:
                end = index
                break
        return _slice_result(path, locator, lines, start, end)
    return None


def _resolve_braced_symbol(
    path: Path, locator: str, symbol: str, lines: list[str]
) -> SourceSlice | None:
    pattern = re.compile(BRACED_SYMBOL.pattern.format(name=re.escape(symbol)))
    for start, line in enumerate(lines):
        if not pattern.match(line):
            continue
        balance = 0
        opened = False
        for index in range(start, len(lines)):
            balance += lines[index].count("{") - lines[index].count("}")
            opened = opened or "{" in lines[index]
            if opened and balance == 0:
                return _slice_result(path, locator, lines, start, index + 1)
        raise ValueError(f"source locator found unbalanced symbol: {locator}")
    return None


def resolve_source_slice(path: Path, locator: str) -> SourceSlice:
    if not path.is_file():
        raise ValueError(f"source locator file is missing: {path}")
    if not isinstance(locator, str) or not locator.strip():
        raise ValueError("source locator is required")
    normalized = locator.strip()
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    if normalized.startswith("heading:"):
        return _resolve_heading(path, normalized, lines)
    if normalized.startswith("symbol:"):
        symbol = normalized.removeprefix("symbol:").strip()
        if not symbol:
            raise ValueError(f"source locator is empty: {normalized}")
        result = _resolve_python_symbol(path, normalized, symbol, lines)
        if result is None:
            result = _resolve_braced_symbol(path, normalized, symbol, lines)
        if result is None:
            raise ValueError(f"source locator did not resolve: {normalized}")
        return result
    raise ValueError(f"unsupported source locator: {normalized}")
