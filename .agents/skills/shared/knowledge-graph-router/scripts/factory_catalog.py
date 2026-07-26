from __future__ import annotations

import fnmatch
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

ROOT = Path(__file__).resolve().parents[5]
CONTRACT_SCRIPTS = ROOT / ".agents/skills/shared/factory-contracts/scripts"
if str(CONTRACT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(CONTRACT_SCRIPTS))
LOOP_SCRIPTS = ROOT / ".agents/skills/loop-engine/scripts"
if str(LOOP_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(LOOP_SCRIPTS))

from artifact_contracts import (  # noqa: E402
    ARTIFACT_FILENAMES,
    is_mutable_implementation_evidence,
    parse_frontmatter,
    source_fingerprint,
)
from graph_profile import GraphProfile  # noqa: E402
from provider import FactoryCatalog, GraphRecord, GraphRelationship  # noqa: E402
from project_knowledge import load_project_knowledge  # noqa: E402
from state_engine import parse_next_task, parse_page_queue  # noqa: E402


PROVENANCE = "EXTRACTED"


def _configured_path(repo_root: Path, key: str, default: str) -> Path:
    config_path = repo_root / ".site-factory/project.json"
    if not config_path.is_file():
        return repo_root / default
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        value = data.get("paths", {}).get(key, default)
    except (OSError, json.JSONDecodeError, AttributeError):
        value = default
    if not isinstance(value, str):
        value = default
    return repo_root / value


def _normalize_key(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or "root"


def _node_id(profile: GraphProfile, node_type: str, key: str) -> str:
    identity_key = key.strip("/") if node_type == "Route" else key
    normalized = _normalize_key(identity_key)
    if (
        node_type not in {"Stage", "Status"}
        and identity_key != normalized
    ):
        suffix = hashlib.sha256(identity_key.encode("utf-8")).hexdigest()[:10]
        normalized = f"{normalized}--{suffix}"
    return f"{profile.project_id}:{node_type}:{normalized}"


def _excluded(relative_path: str, profile: GraphProfile) -> bool:
    return any(
        fnmatch.fnmatchcase(relative_path, pattern)
        or Path(relative_path).match(pattern)
        for pattern in profile.exclude_globs
    )


def _is_migration_evidence(relative_path: str) -> bool:
    return "/migration-archive/" in f"/{relative_path.replace('\\', '/')}"


def _excluded_outside_migration(relative_path: str, profile: GraphProfile) -> bool:
    patterns = tuple(
        pattern
        for pattern in profile.exclude_globs
        if "migration-archive" not in pattern
    )
    return any(
        fnmatch.fnmatchcase(relative_path, pattern)
        or Path(relative_path).match(pattern)
        for pattern in patterns
    )


def _raw_fingerprint(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_source_path(value: str, repo_root: Path) -> str | None:
    normalized = value.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if pure.is_absolute() or any(part == ".." for part in pure.parts):
        return None
    resolved = (repo_root / Path(*pure.parts)).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError:
        return None
    return pure.as_posix()


def _add_record(records: dict[str, GraphRecord], record: GraphRecord) -> None:
    records.setdefault(record.node_id, record)


def _relationship(
    source_id: str, target_id: str, relation_type: str
) -> GraphRelationship:
    return GraphRelationship(
        source_id=source_id,
        target_id=target_id,
        relation_type=relation_type,
        provenance=PROVENANCE,
        confidence=1.0,
    )


def build_factory_catalog(
    profile: GraphProfile,
    repo_root: Path,
    migration_evidence: bool = False,
) -> FactoryCatalog:
    records: dict[str, GraphRecord] = {}
    relationships: set[GraphRelationship] = set()
    known_names = set(ARTIFACT_FILENAMES.values())

    candidates: list[Path] = []
    for artifact_root in profile.artifact_roots:
        root = repo_root / artifact_root
        if root.is_file():
            candidates.append(root)
        elif root.is_dir():
            candidates.extend(root.rglob("*.md"))

    for path in sorted(set(candidates), key=lambda item: item.as_posix().lower()):
        relative = path.resolve().relative_to(repo_root.resolve()).as_posix()
        if path.name not in known_names or _excluded(relative, profile):
            continue
        try:
            metadata, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue

        required = {"schema_version", "page_id", "route", "stage", "status"}
        if not required.issubset(metadata):
            continue
        schema_version = str(metadata["schema_version"])
        fingerprint = source_fingerprint(path, repo_root, schema_version)
        artifact_id = _node_id(profile, "Artifact", relative)
        artifact = GraphRecord(
            node_id=artifact_id,
            project_id=profile.project_id,
            node_type="Artifact",
            source_path=relative,
            source_fingerprint=fingerprint,
            properties={
                "artifact_kind": path.stem,
                "schema_version": schema_version,
                "page_id": metadata["page_id"],
                "route": metadata["route"],
                "stage": metadata["stage"],
                "status": metadata["status"],
                "source_fingerprints": metadata.get("source_fingerprints", {}),
            },
        )
        _add_record(records, artifact)

        dimensions = (
            ("Page", str(metadata["page_id"]), "ARTIFACT_FOR_PAGE"),
            ("Stage", str(metadata["stage"]), "ARTIFACT_FROM_STAGE"),
            ("Status", str(metadata["status"]), "ARTIFACT_HAS_STATUS"),
        )
        for node_type, key, relation_type in dimensions:
            target_id = _node_id(profile, node_type, key)
            _add_record(
                records,
                GraphRecord(
                    node_id=target_id,
                    project_id=profile.project_id,
                    node_type=node_type,
                    source_path=relative,
                    source_fingerprint=fingerprint,
                    properties={"value": key},
                ),
            )
            relationships.add(_relationship(artifact_id, target_id, relation_type))

        page_id = _node_id(profile, "Page", str(metadata["page_id"]))
        route_id = _node_id(profile, "Route", str(metadata["route"]))
        _add_record(
            records,
            GraphRecord(
                node_id=route_id,
                project_id=profile.project_id,
                node_type="Route",
                source_path=relative,
                source_fingerprint=fingerprint,
                properties={"route": metadata["route"]},
            ),
        )
        relationships.add(_relationship(page_id, route_id, "PAGE_HAS_ROUTE"))

        approval = metadata.get("approval")
        if isinstance(approval, dict):
            approval_key = (
                f"{relative}:{approval.get('scope')}:{approval.get('state')}"
            )
            approval_id = _node_id(profile, "Approval", approval_key)
            _add_record(
                records,
                GraphRecord(
                    node_id=approval_id,
                    project_id=profile.project_id,
                    node_type="Approval",
                    source_path=relative,
                    source_fingerprint=fingerprint,
                    properties=dict(approval),
                ),
            )
            relationships.add(
                _relationship(artifact_id, approval_id, "ARTIFACT_HAS_APPROVAL")
            )

        next_inputs = metadata.get("next_stage_inputs")
        if isinstance(next_inputs, list):
            for value in next_inputs:
                if not isinstance(value, str) or not value.strip():
                    continue
                handoff_id = _node_id(
                    profile, "HandoffInput", f"{relative}:{value.strip()}"
                )
                _add_record(
                    records,
                    GraphRecord(
                        node_id=handoff_id,
                        project_id=profile.project_id,
                        node_type="HandoffInput",
                        source_path=relative,
                        source_fingerprint=fingerprint,
                        properties={"input": value.strip()},
                    ),
                )
                relationships.add(
                    _relationship(
                        artifact_id, handoff_id, "ARTIFACT_REQUIRES_NEXT_INPUT"
                    )
                )

        source_fingerprints = metadata.get("source_fingerprints")
        if isinstance(source_fingerprints, dict):
            for source_path, source_digest in sorted(source_fingerprints.items()):
                safe_source = (
                    _safe_source_path(source_path, repo_root)
                    if isinstance(source_path, str)
                    else None
                )
                if (
                    safe_source is None
                    or not isinstance(source_digest, str)
                    or _excluded(safe_source, profile)
                ):
                    continue
                source_id = _node_id(profile, "Source", safe_source)
                mutable_snapshot = is_mutable_implementation_evidence(
                    path.stem, metadata, safe_source
                )
                graph_fingerprint = source_digest
                source_properties = {"path": safe_source}
                if mutable_snapshot and (repo_root / safe_source).is_file():
                    graph_fingerprint = _raw_fingerprint(repo_root / safe_source)
                    source_properties.update(
                        {
                            "recorded_fingerprint": source_digest,
                            "snapshot_state": "historical-migration-evidence",
                        }
                    )
                _add_record(
                    records,
                    GraphRecord(
                        node_id=source_id,
                        project_id=profile.project_id,
                        node_type="Source",
                        source_path=safe_source,
                        source_fingerprint=graph_fingerprint,
                        properties=source_properties,
                    ),
                )
                relationships.add(
                    _relationship(artifact_id, source_id, "ARTIFACT_USES_SOURCE")
                )
                relationships.add(
                    _relationship(page_id, source_id, "PAGE_USES_SOURCE")
                )

    queue_path = _configured_path(repo_root, "page_queue", "docs/site/PAGE_QUEUE.md")
    if queue_path.is_file():
        queue_relative = queue_path.resolve().relative_to(repo_root.resolve()).as_posix()
        queue_fingerprint = _raw_fingerprint(queue_path)
        for page in parse_page_queue(queue_path.read_text(encoding="utf-8")):
            page_id = _node_id(profile, "Page", page.page_id)
            route_id = _node_id(profile, "Route", page.route)
            status_id = _node_id(profile, "Status", page.status)
            stage_id = _node_id(profile, "Stage", page.stage)
            lifecycle_dimensions = (
                (page_id, "Page", {"value": page.page_id, "priority": page.priority}),
                (route_id, "Route", {"route": page.route}),
                (status_id, "Status", {"value": page.status}),
                (stage_id, "Stage", {"value": page.stage}),
            )
            for node_id, node_type, properties in lifecycle_dimensions:
                _add_record(
                    records,
                    GraphRecord(
                        node_id=node_id,
                        project_id=profile.project_id,
                        node_type=node_type,
                        source_path=queue_relative,
                        source_fingerprint=queue_fingerprint,
                        properties=properties,
                    ),
                )
            relationships.update(
                {
                    _relationship(page_id, route_id, "PAGE_HAS_ROUTE"),
                    _relationship(page_id, status_id, "PAGE_HAS_STATUS"),
                    _relationship(page_id, stage_id, "PAGE_HAS_NEXT_STAGE"),
                }
            )

    task_path = _configured_path(repo_root, "next_task", "docs/system/NEXT_TASK.md")
    if task_path.is_file():
        task_relative = task_path.resolve().relative_to(repo_root.resolve()).as_posix()
        task_fingerprint = _raw_fingerprint(task_path)
        task = parse_next_task(task_path.read_text(encoding="utf-8"))
        task_key = f"{task.page}:{task.stage}"
        task_id = _node_id(profile, "NextTask", task_key)
        page_id = _node_id(profile, "Page", task.page)
        stage_id = _node_id(profile, "Stage", task.stage)
        output_id = _node_id(profile, "Artifact", task.output)
        _add_record(
            records,
            GraphRecord(
                node_id=task_id,
                project_id=profile.project_id,
                node_type="NextTask",
                source_path=task_relative,
                source_fingerprint=task_fingerprint,
                properties={
                    "page": task.page,
                    "stage": task.stage,
                    "owner": task.owner,
                    "approval": task.approval,
                    "inputs": task.inputs,
                    "output": task.output,
                },
            ),
        )
        _add_record(
            records,
            GraphRecord(
                node_id=stage_id,
                project_id=profile.project_id,
                node_type="Stage",
                source_path=task_relative,
                source_fingerprint=task_fingerprint,
                properties={"value": task.stage},
            ),
        )
        _add_record(
            records,
            GraphRecord(
                node_id=output_id,
                project_id=profile.project_id,
                node_type="ExpectedArtifact",
                source_path=task_relative,
                source_fingerprint=task_fingerprint,
                properties={"path": task.output},
            ),
        )
        relationships.update(
            {
                _relationship(task_id, page_id, "TASK_FOR_PAGE"),
                _relationship(task_id, stage_id, "TASK_TARGETS_STAGE"),
                _relationship(task_id, output_id, "TASK_OUTPUTS_ARTIFACT"),
                _relationship(page_id, stage_id, "PAGE_HAS_NEXT_STAGE"),
            }
        )

    if migration_evidence:
        for artifact_root in profile.artifact_roots:
            root = repo_root / artifact_root
            if not root.is_dir():
                continue
            for path in root.rglob("*"):
                if not path.is_file() or path.is_symlink():
                    continue
                relative = path.resolve().relative_to(repo_root.resolve()).as_posix()
                if (
                    not _is_migration_evidence(relative)
                    or _excluded_outside_migration(relative, profile)
                ):
                    continue
                evidence_id = _node_id(profile, "MigrationEvidence", relative)
                fingerprint = _raw_fingerprint(path)
                _add_record(
                    records,
                    GraphRecord(
                        node_id=evidence_id,
                        project_id=profile.project_id,
                        node_type="MigrationEvidence",
                        source_path=relative,
                        source_fingerprint=fingerprint,
                        properties={"path": relative, "migration_evidence": True},
                    ),
                )
                parts = PurePosixPath(relative).parts
                if len(parts) >= 3 and parts[:2] == ("docs", "pages"):
                    page_id = _node_id(profile, "Page", f"page-{parts[2]}")
                    relationships.add(
                        _relationship(
                            evidence_id, page_id, "MIGRATION_EVIDENCE_FOR_PAGE"
                        )
                    )

    project_knowledge = load_project_knowledge(profile, repo_root)
    for record in project_knowledge.records:
        _add_record(records, record)
    relationships.update(project_knowledge.relationships)

    return FactoryCatalog(
        records=tuple(sorted(records.values(), key=lambda record: record.node_id)),
        relationships=tuple(
            sorted(
                relationships,
                key=lambda edge: (
                    edge.source_id,
                    edge.relation_type,
                    edge.target_id,
                ),
            )
        ),
    )
