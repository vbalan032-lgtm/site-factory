from __future__ import annotations

from dataclasses import dataclass
import fnmatch
import json
from pathlib import Path, PurePosixPath
import re


SUPPORTED_SCHEMA_VERSIONS = {"1.0"}
SUPPORTED_PROVIDERS = {"graphify-json"}
SECRET_PATH_PATTERN = re.compile(
    r"(?:^|/)(?:\.env(?:\.|$)|[^/]*(?:secret|password|passwd|private[_-]?key|api[_-]?key)[^/]*)",
    re.IGNORECASE,
)


def path_is_secret(value: str) -> bool:
    return bool(SECRET_PATH_PATTERN.search(value.replace("\\", "/")))


@dataclass(frozen=True)
class GraphProfile:
    schema_version: str
    project_id: str
    provider: str
    provider_settings_ref: str | None
    extraction_mode: str
    knowledge_seed_paths: tuple[str, ...]
    benchmark_cases_path: str | None
    corpus_roots: tuple[str, ...]
    exclude_globs: tuple[str, ...]
    artifact_roots: tuple[str, ...]
    output_path: str
    public_locale: str
    freshness_max_age_minutes: int
    entity_aliases: dict[str, tuple[str, ...]]
    ontology_extensions: tuple[str, ...]
    stage_budgets: dict[str, int]


def resolve_repo_path(value: object, field: str, repo_root: Path) -> tuple[str, Path]:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must contain non-empty relative paths")
    raw = value.replace("\\", "/").strip()
    pure = PurePosixPath(raw)
    if pure.is_absolute() or any(part == ".." for part in pure.parts):
        raise ValueError(f"{field} path must stay inside repository: {value}")
    normalized = pure.as_posix()
    resolved = (repo_root / Path(*pure.parts)).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ValueError(f"{field} path must stay inside repository: {value}") from exc
    return normalized, resolved


def _normalized_relative_path(value: object, field: str, repo_root: Path) -> str:
    normalized, _ = resolve_repo_path(value, field, repo_root)
    return normalized


def _string_tuple(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise ValueError(f"{field} must be a list of non-empty strings")
    return tuple(item.strip() for item in value)


def _path_is_within(path: str, root: str) -> bool:
    path_parts = PurePosixPath(path).parts
    root_parts = PurePosixPath(root).parts
    return len(path_parts) >= len(root_parts) and path_parts[: len(root_parts)] == root_parts


def path_is_excluded(path: str, patterns: tuple[str, ...]) -> bool:
    return any(
        fnmatch.fnmatchcase(path, pattern)
        or PurePosixPath(path).match(pattern)
        for pattern in patterns
    )


def load_graph_profile(path: Path, repo_root: Path) -> GraphProfile:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid graph profile: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("graph profile must be a JSON object")

    schema_version = data.get("schema_version")
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise ValueError("unsupported graph profile schema_version")
    project_id = data.get("project_id")
    if not isinstance(project_id, str) or not project_id.strip():
        raise ValueError("project_id is required")
    provider = data.get("provider")
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"unsupported graph provider: {provider}")

    corpus_values = _string_tuple(data.get("corpus_roots"), "corpus_roots")
    corpus_roots = tuple(
        _normalized_relative_path(value, "corpus_roots", repo_root)
        for value in corpus_values
    )
    if not corpus_roots:
        raise ValueError("corpus_roots must not be empty")
    if any(path_is_secret(value) for value in corpus_roots):
        raise ValueError("secret paths cannot be corpus roots")

    exclude_globs = _string_tuple(data.get("exclude_globs"), "exclude_globs")
    if not any(".env" in pattern for pattern in exclude_globs):
        raise ValueError("exclude_globs must exclude secret .env paths")

    artifact_values = _string_tuple(data.get("artifact_roots"), "artifact_roots")
    artifact_roots = tuple(
        _normalized_relative_path(value, "artifact_roots", repo_root)
        for value in artifact_values
    )
    output_path = _normalized_relative_path(
        data.get("output_path"), "output_path", repo_root
    )
    if any(_path_is_within(output_path, root) for root in corpus_roots) and not path_is_excluded(
        output_path, exclude_globs
    ):
        raise ValueError("output_path inside corpus must be explicitly excluded")

    settings_ref = data.get("provider_settings_ref")
    if settings_ref is not None:
        settings_ref = _normalized_relative_path(
            settings_ref, "provider_settings_ref", repo_root
        )
        if path_is_secret(settings_ref):
            raise ValueError("provider_settings_ref must not point to a secret file")

    extraction_mode = data.get("extraction_mode", "semantic")
    if extraction_mode not in {"semantic", "code-only"}:
        raise ValueError("extraction_mode must be semantic or code-only")
    seed_values = data.get("knowledge_seed_paths", [])
    knowledge_seed_paths = tuple(
        _normalized_relative_path(value, "knowledge_seed_paths", repo_root)
        for value in _string_tuple(seed_values, "knowledge_seed_paths")
    )
    if any(path_is_secret(value) for value in knowledge_seed_paths):
        raise ValueError("secret paths cannot be knowledge seeds")
    benchmark_cases = data.get("benchmark_cases_path")
    if benchmark_cases is not None:
        benchmark_cases = _normalized_relative_path(
            benchmark_cases, "benchmark_cases_path", repo_root
        )
        if path_is_secret(benchmark_cases):
            raise ValueError("benchmark_cases_path must not point to a secret file")

    public_locale = data.get("public_locale")
    if not isinstance(public_locale, str) or not public_locale.strip():
        raise ValueError("public_locale is required")
    freshness = data.get("freshness_max_age_minutes")
    if not isinstance(freshness, int) or isinstance(freshness, bool) or freshness <= 0:
        raise ValueError("freshness_max_age_minutes must be a positive integer")

    aliases = data.get("entity_aliases")
    if not isinstance(aliases, dict):
        raise ValueError("entity_aliases must be an object")
    normalized_aliases: dict[str, tuple[str, ...]] = {}
    for entity, values in aliases.items():
        if not isinstance(entity, str) or not entity.strip():
            raise ValueError("entity_aliases keys must be non-empty strings")
        normalized_aliases[entity] = _string_tuple(values, f"entity_aliases.{entity}")

    ontology_extensions = _string_tuple(
        data.get("ontology_extensions"), "ontology_extensions"
    )
    budgets = data.get("stage_budgets")
    if not isinstance(budgets, dict) or not budgets:
        raise ValueError("stage_budgets must be a non-empty object")
    normalized_budgets: dict[str, int] = {}
    for stage, budget in budgets.items():
        if not isinstance(stage, str) or not stage.strip():
            raise ValueError("stage_budgets keys must be non-empty strings")
        if not isinstance(budget, int) or isinstance(budget, bool) or budget <= 0:
            raise ValueError(f"stage budget must be positive: {stage}")
        normalized_budgets[stage] = budget

    return GraphProfile(
        schema_version=schema_version,
        project_id=project_id.strip(),
        provider=provider,
        provider_settings_ref=settings_ref,
        extraction_mode=extraction_mode,
        knowledge_seed_paths=knowledge_seed_paths,
        benchmark_cases_path=benchmark_cases,
        corpus_roots=corpus_roots,
        exclude_globs=exclude_globs,
        artifact_roots=artifact_roots,
        output_path=output_path,
        public_locale=public_locale.strip(),
        freshness_max_age_minutes=freshness,
        entity_aliases=normalized_aliases,
        ontology_extensions=ontology_extensions,
        stage_budgets=normalized_budgets,
    )
