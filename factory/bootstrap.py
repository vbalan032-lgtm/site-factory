from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
import zipfile

from factory.project_config import PROJECT_ID, ProjectConfigError, load_project_config
from factory.snapshot import build_manifest, detect_drift


LOCK_PATH = Path(".site-factory/lock.json")
CONFIG_PATH = Path(".site-factory/project.json")
PACKAGE_PREFIX = "site-factory"
EXCLUDED_PARTS = {".git", ".tmp", ".runtime", "__pycache__", "node_modules", "dist"}
EXCLUDED_NAMES = {"next-env.d.ts"}
PACKAGE_ROOT_DIRECTORIES = (
    ".agents",
    ".github",
    "docs",
    "factory",
    "schemas",
    "templates",
    "tests",
)
PACKAGE_ROOT_FILES = (
    ".gitignore",
    "AGENTS.md",
    "bootstrap.ps1",
    "LICENSE.md",
    "README.md",
    "SECURITY.md",
    "skills-lock.json",
    "THIRD_PARTY_NOTICES.md",
)
SECRET_FILE_MARKERS = (
    "api-key",
    "api_key",
    "api-token",
    "api_token",
    "client-secret",
    "client_secret",
    "credential",
    "id_ed25519",
    "id_rsa",
    "oauth",
    "password",
    "passwd",
    "private-key",
    "private_key",
    "secret",
    "token",
)
SECRET_SUFFIXES = (".key", ".p12", ".pfx", ".pem")
SECRET_DIRECTORY_NAMES = {".secrets", "credentials", "secrets"}


class BootstrapError(RuntimeError):
    pass


@dataclass(frozen=True)
class OperationResult:
    actions: tuple[str, ...]
    changed: bool = False


@dataclass(frozen=True)
class DoctorReport:
    ok: bool
    issues: tuple[str, ...]


@dataclass(frozen=True)
class PackageResult:
    archive: Path
    checksum: Path
    manifest: Path


def _version(source_root: Path) -> str:
    path = source_root / "factory/dependencies.lock.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        value = data["factory_version"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as exc:
        raise BootstrapError("factory dependency lock is missing or invalid") from exc
    if not isinstance(value, str) or not value:
        raise BootstrapError("factory_version is missing")
    return value


def _read_lock(target: Path) -> dict:
    try:
        data = json.loads((target / LOCK_PATH).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise BootstrapError("factory lock is missing or invalid") from exc
    if data.get("schema_version") != "1.0" or not isinstance(data.get("installed_files"), dict):
        raise BootstrapError("factory lock schema is invalid")
    return data


def _profile_paths(source_root: Path, profiles: tuple[str, ...] | list[str] | None) -> tuple[tuple[str, ...], tuple[str, ...]]:
    try:
        data = json.loads((source_root / "factory/profiles.json").read_text(encoding="utf-8"))
        definitions = data["profiles"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as exc:
        raise BootstrapError("factory profiles are missing or invalid") from exc
    selected = tuple(profiles or data.get("default_profiles", ()))
    if not selected:
        raise BootstrapError("at least one factory profile is required")
    unknown = [name for name in selected if name not in definitions]
    if unknown:
        raise BootstrapError("unknown factory profile: " + ", ".join(unknown))
    paths: list[str] = []
    for name in selected:
        values = definitions[name].get("owned_paths", [])
        if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
            raise BootstrapError(f"factory profile {name} has invalid owned_paths")
        paths.extend(values)
    return selected, tuple(dict.fromkeys(paths))


def _validate_identity(project_id: str, project_name: str) -> None:
    if not isinstance(project_id, str) or not PROJECT_ID.fullmatch(project_id):
        raise BootstrapError("project_id must use lowercase kebab-case")
    if not isinstance(project_name, str) or not project_name.strip():
        raise BootstrapError("project_name must be a non-empty string")


def _write_json_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _source_manifest(source_root: Path, owned_paths: tuple[str, ...]) -> dict[str, str]:
    return build_manifest(source_root, owned_paths)


def _write_lock(
    source_root: Path,
    target: Path,
    profiles: tuple[str, ...],
    owned_paths: tuple[str, ...],
    *,
    source: str = "site-factory release snapshot",
) -> None:
    manifest = build_manifest(target, owned_paths)
    _write_json_atomic(
        target / LOCK_PATH,
        {
            "schema_version": "1.0",
            "factory_version": _version(source_root),
            "source": source,
            "profiles": list(profiles),
            "owned_roots": list(owned_paths),
            "installed_files": manifest,
        },
    )


def _copy_owned_snapshot(
    source_root: Path,
    target: Path,
    owned_paths: tuple[str, ...],
    *,
    allow_replace: bool,
) -> None:
    manifest = _source_manifest(source_root, owned_paths)
    collisions = [relative for relative in manifest if (target / relative).exists()]
    if collisions and not allow_replace:
        sample = ", ".join(collisions[:3])
        raise BootstrapError(f"factory-owned file collision: {sample}")
    for relative in sorted(manifest):
        source = source_root / relative
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def _unique_backup_path(target: Path, name: str) -> Path:
    base = target / ".site-factory/backups" / name
    candidate = base
    sequence = 2
    while candidate.exists():
        candidate = base.with_name(f"{base.stem}-{sequence}{base.suffix}")
        sequence += 1
    return candidate


def _backup_installed_snapshot(target: Path, lock: dict) -> Path:
    version = str(lock.get("factory_version", "unknown"))
    backup_path = _unique_backup_path(target, f"pre-update-{version}.zip")
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        backup_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for relative in sorted(lock["installed_files"]):
            source = target / Path(*PurePosixPath(relative).parts)
            if source.is_file():
                archive.write(source, PurePosixPath(relative).as_posix())
        archive.write(target / LOCK_PATH, LOCK_PATH.as_posix())
    return backup_path


def _restore_installed_snapshot(
    target: Path,
    backup_path: Path,
    old_files: set[str],
    new_files: set[str],
) -> None:
    for relative in sorted(new_files - old_files):
        path = target / Path(*PurePosixPath(relative).parts)
        if path.is_file() or path.is_symlink():
            path.unlink()
    with zipfile.ZipFile(backup_path) as archive:
        for relative in sorted(old_files | {LOCK_PATH.as_posix()}):
            destination = target / Path(*PurePosixPath(relative).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_name(destination.name + ".rollback.tmp")
            temporary.write_bytes(archive.read(relative))
            temporary.replace(destination)


def _customize_config(
    target: Path,
    project_id: str,
    project_name: str,
    *,
    update_template_identity: bool = False,
) -> None:
    path = target / CONFIG_PATH
    data = json.loads(path.read_text(encoding="utf-8"))
    data["project_id"] = project_id
    data["project_name"] = project_name
    _write_json_atomic(path, data)
    config = load_project_config(target)
    if update_template_identity:
        for key in ("graph_profile", "project_knowledge"):
            identity_path = target / config.path(key)
            if identity_path.is_file():
                identity = json.loads(identity_path.read_text(encoding="utf-8"))
                identity["project_id"] = project_id
                _write_json_atomic(identity_path, identity)
        package_path = target / "package.json"
        if package_path.is_file():
            package = json.loads(package_path.read_text(encoding="utf-8"))
            package["name"] = project_id
            package["private"] = True
            _write_json_atomic(package_path, package)
        package_lock_path = target / "package-lock.json"
        if package_lock_path.is_file():
            package_lock = json.loads(package_lock_path.read_text(encoding="utf-8"))
            package_lock["name"] = project_id
            root_package = package_lock.get("packages", {}).get("")
            if isinstance(root_package, dict):
                root_package["name"] = project_id
            _write_json_atomic(package_lock_path, package_lock)


def new_project(
    source_root: Path,
    target: Path,
    project_id: str,
    project_name: str,
    *,
    profiles: tuple[str, ...] | list[str] | None = None,
    apply: bool,
) -> OperationResult:
    source_root = source_root.resolve()
    target = target.resolve()
    actions = ("create starter", "install factory skills", "write project config and lock")
    _validate_identity(project_id, project_name)
    selected_profiles, owned_paths = _profile_paths(source_root, profiles)
    if target.exists() and any(target.iterdir()):
        raise BootstrapError("New target must be absent or empty")
    if not apply:
        return OperationResult(actions)
    target.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        source_root / "templates/nextjs",
        target,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(
            "node_modules", ".next", ".tmp", ".runtime", "__pycache__", "*.pyc"
        ),
    )
    _customize_config(
        target, project_id, project_name, update_template_identity=True
    )
    _copy_owned_snapshot(source_root, target, owned_paths, allow_replace=False)
    _write_lock(source_root, target, selected_profiles, owned_paths)
    return OperationResult(actions, changed=True)


def attach_project(
    source_root: Path,
    target: Path,
    project_id: str,
    project_name: str,
    *,
    profiles: tuple[str, ...] | list[str] | None = None,
    apply: bool,
) -> OperationResult:
    source_root = source_root.resolve()
    target = target.resolve()
    actions = ("attach factory skills", "create project config", "write factory lock")
    _validate_identity(project_id, project_name)
    selected_profiles, owned_paths = _profile_paths(source_root, profiles)
    if not target.is_dir():
        raise BootstrapError("Attach target must be an existing directory")
    if (target / CONFIG_PATH).exists() or (target / LOCK_PATH).exists():
        raise BootstrapError("target is already attached; use Update")
    source_manifest = _source_manifest(source_root, owned_paths)
    collisions = [relative for relative in source_manifest if (target / relative).exists()]
    if collisions:
        raise BootstrapError(f"factory-owned file collision: {', '.join(collisions[:3])}")
    if not apply:
        return OperationResult(actions)
    config_source = source_root / "templates/nextjs" / CONFIG_PATH
    config_target = target / CONFIG_PATH
    config_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(config_source, config_target)
    _customize_config(target, project_id, project_name)
    _copy_owned_snapshot(source_root, target, owned_paths, allow_replace=False)
    _write_lock(source_root, target, selected_profiles, owned_paths)
    return OperationResult(actions, changed=True)


def adopt_project(
    source_root: Path,
    target: Path,
    project_id: str,
    project_name: str,
    *,
    profiles: tuple[str, ...] | list[str] | None = None,
    apply: bool,
) -> OperationResult:
    source_root = source_root.resolve()
    target = target.resolve()
    actions = (
        "adopt legacy factory snapshot",
        "create project config",
        "write factory lock",
    )
    _validate_identity(project_id, project_name)
    selected_profiles, owned_paths = _profile_paths(source_root, profiles)
    if not target.is_dir():
        raise BootstrapError("Adopt target must be an existing directory")
    if (target / CONFIG_PATH).exists() or (target / LOCK_PATH).exists():
        raise BootstrapError("target is already attached; use Update")
    legacy_manifest = build_manifest(target, owned_paths)
    if not legacy_manifest:
        raise BootstrapError("Adopt target has no factory-owned files for selected profiles")
    if not apply:
        return OperationResult(actions)
    config_source = source_root / "templates/nextjs" / CONFIG_PATH
    config_target = target / CONFIG_PATH
    config_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(config_source, config_target)
    _customize_config(target, project_id, project_name)
    _write_lock(
        source_root,
        target,
        selected_profiles,
        owned_paths,
        source="legacy project snapshot",
    )
    return OperationResult(actions, changed=True)


def update_project(source_root: Path, target: Path, *, apply: bool) -> OperationResult:
    source_root = source_root.resolve()
    target = target.resolve()
    lock = _read_lock(target)
    selected_profiles, owned_paths = _profile_paths(source_root, lock.get("profiles"))
    drift = detect_drift(target, lock["installed_files"])
    if drift:
        raise BootstrapError("local factory drift blocks update: " + ", ".join(drift[:5]))
    new_manifest = _source_manifest(source_root, owned_paths)
    old_files = set(lock["installed_files"])
    new_files = set(new_manifest)
    collisions = [
        relative
        for relative in sorted(new_files - old_files)
        if (target / Path(*PurePosixPath(relative).parts)).exists()
    ]
    if collisions:
        raise BootstrapError("new release collision: " + ", ".join(collisions[:5]))
    actions = (
        "back up current factory snapshot",
        f"update factory snapshot to {_version(source_root)}",
        "rewrite factory lock",
    )
    if not apply:
        return OperationResult(actions)

    backup_path = _backup_installed_snapshot(target, lock)
    obsolete = sorted(old_files - new_files)
    try:
        _copy_owned_snapshot(source_root, target, owned_paths, allow_replace=True)
        for relative in obsolete:
            path = target / Path(*PurePosixPath(relative).parts)
            if path.is_file():
                path.unlink()
        _write_lock(source_root, target, selected_profiles, owned_paths)
    except Exception as exc:
        try:
            _restore_installed_snapshot(target, backup_path, old_files, new_files)
        except Exception as rollback_exc:
            raise BootstrapError(
                f"factory update failed and rollback also failed: {rollback_exc}"
            ) from exc
        raise BootstrapError("factory update failed and was rolled back") from exc
    return OperationResult(actions, changed=True)


def doctor(target: Path) -> DoctorReport:
    target = target.resolve()
    issues: list[str] = []
    try:
        config = load_project_config(target)
    except ProjectConfigError as exc:
        issues.append(f"project config: {exc}")
        config = None
    try:
        lock = _read_lock(target)
    except BootstrapError as exc:
        issues.append(str(exc))
        lock = None
    if lock is not None:
        drift = detect_drift(target, lock["installed_files"])
        if drift:
            issues.append("factory drift: " + ", ".join(drift[:5]))
    if config is not None:
        required_files = (
            "master_context",
            "brand",
            "product",
            "claims",
            "personas",
            "business_architecture",
            "sitemap",
            "tech_stack",
            "codex_environment",
            "page_queue",
            "next_task",
            "status",
            "loop_log",
            "graph_profile",
            "project_knowledge",
        )
        required_directories = ("source_index",)
        wrong_files = [
            config.path(key).as_posix()
            for key in required_files
            if not (target / config.path(key)).is_file()
        ]
        wrong_directories = [
            config.path(key).as_posix()
            for key in required_directories
            if not (target / config.path(key)).is_dir()
        ]
        if wrong_files:
            issues.append("configured source paths must be files: " + ", ".join(wrong_files))
        if wrong_directories:
            issues.append(
                "configured source paths must be directories: "
                + ", ".join(wrong_directories)
            )
        for key in ("graph_profile", "project_knowledge"):
            identity_path = target / config.path(key)
            if not identity_path.is_file():
                continue
            try:
                identity = json.loads(identity_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                issues.append(f"configured {key} is invalid JSON")
                continue
            if identity.get("project_id") != config.project_id:
                issues.append(f"configured {key} project_id does not match project config")
    return DoctorReport(not issues, tuple(issues))


def configure_codex(target: Path, *, apply: bool) -> OperationResult:
    target = target.resolve()
    actions = ("write project-scoped Codex example",)
    if not apply:
        return OperationResult(actions)
    path = target / ".site-factory/codex-config.example.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        backup_root = target / ".site-factory/backups"
        backup_root.mkdir(parents=True, exist_ok=True)
        backup = backup_root / "codex-config.example.toml"
        sequence = 2
        while backup.exists():
            backup = backup_root / f"codex-config.example-{sequence}.toml"
            sequence += 1
        shutil.copy2(path, backup)
    path.write_text(
        "# Site Factory keeps its portable skills in .agents/skills.\n"
        "# Open Codex from the project root so project skills and AGENTS.md are discovered.\n"
        "# Copy only settings verified against the current Codex config reference.\n"
        "# Credentials and user-specific absolute paths do not belong in this file.\n",
        encoding="utf-8",
    )
    return OperationResult(actions, changed=True)


def _is_secret_or_private(relative: Path) -> bool:
    parts = tuple(part.casefold() for part in relative.parts)
    name = parts[-1]
    if ".site-factory" in parts and "backups" in parts:
        return True
    if any(part in SECRET_DIRECTORY_NAMES for part in parts[:-1]):
        return True
    if name.startswith(".env") and name != ".env.example":
        return True
    if name.endswith(SECRET_SUFFIXES):
        return True
    return any(marker in name for marker in SECRET_FILE_MARKERS)


def _is_reparse_point(path: Path) -> bool:
    if path.is_symlink() or path.is_junction():
        return True
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError as exc:
        raise BootstrapError(f"cannot inspect release package path: {path}") from exc
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & reparse_flag)


def _reject_unsafe_package_path(path: Path, source_root: Path) -> None:
    relative = path.relative_to(source_root)
    if _is_reparse_point(path):
        raise BootstrapError(
            "symbolic links, junctions, and reparse points are not allowed in "
            f"release packages: {relative.as_posix()}"
        )
    if not path.resolve().is_relative_to(source_root):
        raise BootstrapError(
            f"release package path escapes source root: {relative.as_posix()}"
        )


def _package_files(source_root: Path, output_root: Path) -> list[Path]:
    files: list[Path] = []
    output_root = output_root.resolve()
    candidates = [source_root / name for name in PACKAGE_ROOT_FILES]
    candidates.extend(source_root / name for name in PACKAGE_ROOT_DIRECTORIES)
    for candidate in candidates:
        _reject_unsafe_package_path(candidate, source_root)
        if candidate.is_file():
            files.append(candidate)
            continue
        if not candidate.is_dir():
            continue
        for current, directories, names in os.walk(candidate):
            current_path = Path(current)
            safe_directories: list[str] = []
            for directory in sorted(directories):
                path = current_path / directory
                relative = path.relative_to(source_root)
                _reject_unsafe_package_path(path, source_root)
                if directory in EXCLUDED_PARTS or _is_secret_or_private(relative):
                    continue
                if path.resolve().is_relative_to(output_root):
                    continue
                safe_directories.append(directory)
            directories[:] = safe_directories
            for name in sorted(names):
                if name in EXCLUDED_NAMES or name.endswith((".pyc", ".tsbuildinfo")):
                    continue
                path = current_path / name
                relative = path.relative_to(source_root)
                _reject_unsafe_package_path(path, source_root)
                if _is_secret_or_private(relative):
                    continue
                if path.resolve().is_relative_to(output_root):
                    continue
                files.append(path)
    return sorted(files, key=lambda item: item.relative_to(source_root).as_posix())


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pack_distribution(source_root: Path, output_root: Path) -> PackageResult:
    source_root = source_root.resolve()
    output_root = output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    version = _version(source_root)
    base = f"site-factory-v{version}"
    archive = output_root / f"{base}.zip"
    checksum = output_root / f"{base}.zip.sha256"
    manifest_path = output_root / f"{base}.manifest.json"
    files = _package_files(source_root, output_root)
    manifest = {
        "schema_version": "1.0",
        "factory_version": version,
        "files": {
            path.relative_to(source_root).as_posix(): "sha256:" + _sha256(path.read_bytes())
            for path in files
        },
    }
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    manifest_path.write_bytes(manifest_bytes)

    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in files:
            relative = path.relative_to(source_root).as_posix()
            info = zipfile.ZipInfo(f"{PACKAGE_PREFIX}/{relative}", date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, path.read_bytes(), compresslevel=9)
        info = zipfile.ZipInfo(f"{PACKAGE_PREFIX}/MANIFEST.json", date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        bundle.writestr(info, manifest_bytes, compresslevel=9)

    digest = _sha256(archive.read_bytes())
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="ascii")
    return PackageResult(archive, checksum, manifest_path)


def verify_package(archive: Path, checksum: Path, manifest_path: Path) -> DoctorReport:
    issues: list[str] = []
    try:
        checksum_parts = checksum.read_text(encoding="ascii").split()
        expected_checksum = checksum_parts[0]
        if len(checksum_parts) < 2 or checksum_parts[1] != archive.name:
            issues.append("checksum filename does not match archive")
        if _sha256(archive.read_bytes()) != expected_checksum:
            issues.append("archive checksum mismatch")
        manifest_bytes = manifest_path.read_bytes()
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, IndexError) as exc:
        return DoctorReport(False, (f"package metadata is invalid: {exc}",))
    if set(manifest) != {"schema_version", "factory_version", "files"}:
        issues.append("package manifest schema is invalid")
    if manifest.get("schema_version") != "1.0":
        issues.append("package manifest schema_version is invalid")
    version = manifest.get("factory_version")
    if not isinstance(version, str) or archive.name != f"site-factory-v{version}.zip":
        issues.append("archive filename does not match manifest factory_version")
    manifest_files = manifest.get("files")
    if not isinstance(manifest_files, dict):
        return DoctorReport(False, tuple(issues + ["package manifest files are invalid"]))
    invalid_paths = []
    for relative, expected in manifest_files.items():
        pure = PurePosixPath(relative) if isinstance(relative, str) else PurePosixPath("..")
        if (
            not isinstance(relative, str)
            or pure.is_absolute()
            or ".." in pure.parts
            or "\\" in relative
            or not isinstance(expected, str)
            or not expected.startswith("sha256:")
            or len(expected) != 71
            or any(character not in "0123456789abcdef" for character in expected[7:])
        ):
            invalid_paths.append(str(relative))
    if invalid_paths:
        issues.append("package manifest entries are invalid: " + ", ".join(invalid_paths[:5]))
    try:
        with zipfile.ZipFile(archive) as bundle:
            names = bundle.namelist()
            if len(names) != len(set(names)):
                issues.append("package contains duplicate entries")
            expected_names = {
                f"{PACKAGE_PREFIX}/{relative}" for relative in manifest_files
            } | {f"{PACKAGE_PREFIX}/MANIFEST.json"}
            actual_names = set(names)
            extras = sorted(actual_names - expected_names)
            missing = sorted(expected_names - actual_names)
            if extras:
                issues.append("package contains unexpected entries: " + ", ".join(extras[:5]))
            if missing:
                issues.append("package entries are missing: " + ", ".join(missing[:5]))
            embedded_name = f"{PACKAGE_PREFIX}/MANIFEST.json"
            if embedded_name in actual_names and bundle.read(embedded_name) != manifest_bytes:
                issues.append("embedded manifest does not match external manifest")
            for relative, expected in manifest_files.items():
                name = f"{PACKAGE_PREFIX}/{relative}"
                if name not in actual_names:
                    continue
                actual = "sha256:" + _sha256(bundle.read(name))
                if actual != expected:
                    issues.append(f"package file checksum mismatch: {relative}")
    except (OSError, zipfile.BadZipFile) as exc:
        issues.append(f"archive is invalid: {exc}")
    return DoctorReport(not issues, tuple(issues))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Site Factory Windows bootstrap")
    parser.add_argument("mode", choices=("new", "attach", "adopt", "doctor", "update", "configure-codex", "pack", "verify"))
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--target", type=Path)
    parser.add_argument("--project-id")
    parser.add_argument("--project-name")
    parser.add_argument("--profiles", help="Comma-separated factory profiles")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--checksum", type=Path)
    parser.add_argument("--manifest", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.mode in {"new", "attach", "adopt"}:
            if not args.target or not args.project_id or not args.project_name:
                raise BootstrapError("target, project-id and project-name are required")
            operations = {
                "new": new_project,
                "attach": attach_project,
                "adopt": adopt_project,
            }
            operation = operations[args.mode]
            profiles = tuple(item.strip() for item in args.profiles.split(",")) if args.profiles else None
            result = operation(
                args.source,
                args.target,
                args.project_id,
                args.project_name,
                profiles=profiles,
                apply=args.apply,
            )
        elif args.mode == "update":
            if not args.target:
                raise BootstrapError("target is required")
            result = update_project(args.source, args.target, apply=args.apply)
        elif args.mode == "doctor":
            if not args.target:
                raise BootstrapError("target is required")
            report = doctor(args.target)
            for issue in report.issues:
                print(f"ERROR: {issue}")
            if report.ok:
                print("OK: factory installation is healthy")
            return 0 if report.ok else 1
        elif args.mode == "configure-codex":
            if not args.target:
                raise BootstrapError("target is required")
            result = configure_codex(args.target, apply=args.apply)
        elif args.mode == "pack":
            if not args.apply:
                print(
                    "DRY-RUN: create deterministic release package in "
                    + str((args.output or args.source / "dist").resolve())
                )
                return 0
            package = pack_distribution(args.source, args.output or args.source / "dist")
            print(package.archive)
            print(package.checksum)
            print(package.manifest)
            return 0
        else:
            if not args.archive or not args.checksum or not args.manifest:
                raise BootstrapError("archive, checksum and manifest are required")
            report = verify_package(args.archive, args.checksum, args.manifest)
            for issue in report.issues:
                print(f"ERROR: {issue}")
            return 0 if report.ok else 1
        prefix = "APPLY" if result.changed else "DRY-RUN"
        for action in result.actions:
            print(f"{prefix}: {action}")
        return 0
    except (BootstrapError, ProjectConfigError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
