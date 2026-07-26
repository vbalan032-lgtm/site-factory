from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re

from graph_profile import GraphProfile, path_is_excluded, path_is_secret
from provider import FactoryCatalog, GraphRecord, GraphRelationship


SUPPORTED_SCHEMA_VERSIONS = {"1.0"}
BASE_NODE_TYPES = {
    "Project",
    "Document",
    "Source",
    "Artifact",
    "Page",
    "Route",
    "Entity",
    "Offer",
    "Audience",
    "Claim",
    "Evidence",
    "Decision",
    "Approval",
    "Stage",
    "Status",
    "HandoffInput",
    "Section",
    "Component",
    "Asset",
}
PROVENANCE = {"EXTRACTED", "INFERRED", "AMBIGUOUS"}


def _normalize_key(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or "root"


def _node_id(project_id: str, node_type: str, key: str) -> str:
    normalized = _normalize_key(key)
    if key != normalized:
        suffix = hashlib.sha256(key.encode("utf-8")).hexdigest()[:10]
        normalized = f"{normalized}--{suffix}"
    return f"{project_id}:{node_type}:{normalized}"


def _fingerprint(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_source(value: object, repo_root: Path, profile: GraphProfile) -> tuple[str, Path]:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("knowledge node source_path is required")
    normalized = value.replace("\\", "/").strip()
    pure = PurePosixPath(normalized)
    if pure.is_absolute() or any(part == ".." for part in pure.parts):
        raise ValueError(f"knowledge source escapes repository: {value}")
    if path_is_secret(normalized) or path_is_excluded(normalized, profile.exclude_globs):
        raise ValueError(f"knowledge source is excluded: {value}")
    path = (repo_root / Path(*pure.parts)).resolve()
    try:
        path.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ValueError(f"knowledge source escapes repository: {value}") from exc
    if not path.is_file():
        raise ValueError(f"knowledge source is missing: {value}")
    return pure.as_posix(), path


def load_project_knowledge(profile: GraphProfile, repo_root: Path) -> FactoryCatalog:
    records: dict[str, GraphRecord] = {}
    relationships: set[GraphRelationship] = set()
    references: dict[str, str] = {}
    pending_edges: list[dict[str, object]] = []
    allowed_types = BASE_NODE_TYPES | set(profile.ontology_extensions)

    for configured in profile.knowledge_seed_paths:
        seed_path = (repo_root / configured).resolve()
        try:
            seed_path.relative_to(repo_root.resolve())
        except ValueError as exc:
            raise ValueError("knowledge seed escapes repository") from exc
        try:
            data = json.loads(seed_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid knowledge seed {configured}: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError("knowledge seed must be an object")
        if data.get("schema_version") not in SUPPORTED_SCHEMA_VERSIONS:
            raise ValueError("unsupported knowledge seed schema_version")
        if data.get("project_id") != profile.project_id:
            raise ValueError("knowledge seed project_id does not match profile")
        nodes = data.get("nodes")
        edges = data.get("relationships", [])
        if not isinstance(nodes, list) or not isinstance(edges, list):
            raise ValueError("knowledge seed nodes and relationships must be lists")

        for raw in nodes:
            if not isinstance(raw, dict):
                raise ValueError("knowledge node must be an object")
            node_type = raw.get("type")
            key = raw.get("key")
            label = raw.get("label")
            summary = raw.get("summary")
            if node_type not in allowed_types:
                raise ValueError(f"unsupported knowledge node type: {node_type}")
            if not all(isinstance(value, str) and value.strip() for value in (key, label, summary)):
                raise ValueError("knowledge node key, label and summary are required")
            reference = f"{node_type}:{key}"
            if reference in references:
                raise ValueError(f"duplicate knowledge node: {reference}")
            source_path, source = _safe_source(raw.get("source_path"), repo_root, profile)
            node_id = _node_id(profile.project_id, node_type, key)
            properties = {
                "label": label.strip(),
                "summary": summary.strip(),
                "source_location": raw.get("source_location"),
                "routes": raw.get("routes", []),
                "stages": raw.get("stages", []),
                "tags": raw.get("tags", []),
            }
            records[node_id] = GraphRecord(
                node_id=node_id,
                project_id=profile.project_id,
                node_type=node_type,
                source_path=source_path,
                source_fingerprint=_fingerprint(source),
                properties=properties,
            )
            references[reference] = node_id
        pending_edges.extend(edge for edge in edges if isinstance(edge, dict))

    for raw in pending_edges:
        source_ref = raw.get("source")
        target_ref = raw.get("target")
        relation = raw.get("relation")
        provenance = raw.get("provenance", "EXTRACTED")
        confidence = raw.get("confidence", 1.0)
        if source_ref not in references or target_ref not in references:
            raise ValueError(f"knowledge relationship endpoint is missing: {source_ref} -> {target_ref}")
        if not isinstance(relation, str) or not relation.strip():
            raise ValueError("knowledge relationship relation is required")
        if provenance not in PROVENANCE:
            raise ValueError(f"unsupported knowledge provenance: {provenance}")
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
            raise ValueError("knowledge relationship confidence must be numeric")
        numeric_confidence = float(confidence)
        if not 0 <= numeric_confidence <= 1:
            raise ValueError("knowledge relationship confidence must be between 0 and 1")
        relationships.add(
            GraphRelationship(
                source_id=references[str(source_ref)],
                target_id=references[str(target_ref)],
                relation_type=relation.strip(),
                provenance=str(provenance),
                confidence=numeric_confidence,
            )
        )

    return FactoryCatalog(
        records=tuple(sorted(records.values(), key=lambda record: record.node_id)),
        relationships=tuple(
            sorted(
                relationships,
                key=lambda edge: (edge.source_id, edge.relation_type, edge.target_id),
            )
        ),
    )
