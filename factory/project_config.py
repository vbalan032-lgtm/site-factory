from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
import re


CONFIG_PATH = Path(".site-factory/project.json")
REQUIRED_PATHS = {
    "master_context",
    "brand",
    "product",
    "claims",
    "personas",
    "business_architecture",
    "sitemap",
    "tech_stack",
    "codex_environment",
    "source_index",
    "page_queue",
    "next_task",
    "status",
    "loop_log",
    "graph_profile",
    "project_knowledge",
}
PROJECT_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SUPPORTED_TECH_PROFILES = ("nextjs-16", "static-html")


class ProjectConfigError(ValueError):
    pass


@dataclass(frozen=True)
class ProjectConfig:
    schema_version: str
    project_id: str
    project_name: str
    public_language: str
    accepted_latin_terms: tuple[str, ...]
    tech_profile: str
    paths: dict[str, Path]

    def path(self, key: str) -> Path:
        try:
            return self.paths[key]
        except KeyError as exc:
            raise ProjectConfigError(f"unknown configured path: {key}") from exc


def _repository_path(value: object, key: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ProjectConfigError(f"path {key} must be a non-empty string")
    normalized = value.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if pure.is_absolute() or ".." in pure.parts or ":" in normalized:
        raise ProjectConfigError(f"path {key} must be repository-relative")
    return Path(*pure.parts)


def load_project_config(repo_root: Path) -> ProjectConfig:
    path = repo_root / CONFIG_PATH
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProjectConfigError(f"project config is missing: {CONFIG_PATH.as_posix()}") from exc
    except json.JSONDecodeError as exc:
        raise ProjectConfigError(f"project config is invalid JSON: {exc}") from exc

    if data.get("schema_version") != "1.0":
        raise ProjectConfigError("schema_version must be 1.0")
    project_id = data.get("project_id")
    if not isinstance(project_id, str) or not PROJECT_ID.fullmatch(project_id):
        raise ProjectConfigError("project_id must use lowercase kebab-case")
    project_name = data.get("project_name")
    if not isinstance(project_name, str) or not project_name.strip():
        raise ProjectConfigError("project_name must be a non-empty string")
    if data.get("public_language") != "ru-Cyrl":
        raise ProjectConfigError("public_language must be ru-Cyrl in schema 1.0")
    tech_profile = data.get("tech_profile")
    if tech_profile not in SUPPORTED_TECH_PROFILES:
        raise ProjectConfigError(
            "tech_profile must be one of: " + ", ".join(SUPPORTED_TECH_PROFILES)
        )
    terms = data.get("accepted_latin_terms", [])
    if not isinstance(terms, list) or not all(
        isinstance(term, str) and term.strip() for term in terms
    ):
        raise ProjectConfigError("accepted_latin_terms must be a list of strings")
    raw_paths = data.get("paths")
    if not isinstance(raw_paths, dict):
        raise ProjectConfigError("paths must be an object")
    missing = REQUIRED_PATHS - raw_paths.keys()
    if missing:
        raise ProjectConfigError("missing configured paths: " + ", ".join(sorted(missing)))
    paths = {key: _repository_path(raw_paths[key], key) for key in REQUIRED_PATHS}

    return ProjectConfig(
        schema_version="1.0",
        project_id=project_id,
        project_name=project_name.strip(),
        public_language="ru-Cyrl",
        accepted_latin_terms=tuple(terms),
        tech_profile=tech_profile,
        paths=paths,
    )
