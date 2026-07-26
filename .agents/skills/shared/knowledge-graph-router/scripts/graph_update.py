from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil

from graph_profile import GraphProfile, path_is_excluded, path_is_secret
from provider import FactoryCatalog


def _corpus_rule(profile: GraphProfile, source_path: str):
    path_parts = PurePosixPath(source_path).parts
    matches = []
    for rule in profile.corpus_rules:
        root_parts = PurePosixPath(rule.root).parts
        if path_parts[: len(root_parts)] == root_parts:
            matches.append((len(root_parts), rule))
    return max(matches, key=lambda item: item[0])[1] if matches else None


def _normalize_graphify_source(value: object, repo_root: Path) -> str:
    if not isinstance(value, str) or not value.strip():
        return ""
    raw = value.strip().replace("\\", "/")
    staging = (repo_root / "graphify-out/.corpus").resolve()
    candidate = Path(value)
    if candidate.is_absolute():
        try:
            return candidate.resolve().relative_to(staging).as_posix()
        except ValueError:
            try:
                return candidate.resolve().relative_to(repo_root.resolve()).as_posix()
            except ValueError:
                return ""
    staging_prefix = staging.as_posix().rstrip("/") + "/"
    if raw.lower().startswith(staging_prefix.lower()):
        return raw[len(staging_prefix) :]
    return PurePosixPath(raw).as_posix()


def collect_profile_files(profile: GraphProfile, repo_root: Path) -> tuple[str, ...]:
    root_resolved = repo_root.resolve()
    included: set[str] = set()
    for configured in profile.corpus_roots:
        configured_rule = _corpus_rule(profile, configured)
        if configured_rule is not None and configured_rule.index_mode == "excluded":
            continue
        source = (root_resolved / configured).resolve()
        try:
            source.relative_to(root_resolved)
        except ValueError:
            continue
        candidates = [source] if source.is_file() else source.rglob("*") if source.is_dir() else []
        for path in candidates:
            if not path.is_file() or path.is_symlink():
                continue
            relative = path.resolve().relative_to(root_resolved).as_posix()
            if not path_is_excluded(relative, profile.exclude_globs) and not path_is_secret(relative):
                included.add(relative)
    return tuple(sorted(included))


def materialize_profile_corpus(
    profile: GraphProfile, repo_root: Path
) -> tuple[Path, tuple[str, ...]]:
    root_resolved = repo_root.resolve()
    staging = (root_resolved / "graphify-out/.corpus").resolve()
    staging.relative_to(root_resolved)
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    included = collect_profile_files(profile, root_resolved)
    for relative in included:
        destination = staging / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root_resolved / relative, destination)
    return staging, included


def _raw_fingerprint(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _record_is_publishable(record, profile: GraphProfile, repo_root: Path, allowed: set[str]) -> bool:
    if record.project_id != profile.project_id or record.source_path not in allowed:
        return False
    if record.node_type != "Source" or not isinstance(record.source_fingerprint, str):
        return True
    from fingerprints import current_source_fingerprints

    return record.source_fingerprint in current_source_fingerprints(
        repo_root / record.source_path, repo_root
    )


def _existing_graph_is_healthy(
    target_path: Path, profile: GraphProfile, repo_root: Path
) -> bool:
    try:
        existing = json.loads(target_path.read_text(encoding="utf-8"))
        nodes = existing["nodes"]
        metadata = existing["factory_metadata"]
        manifest = metadata["source_fingerprints"]
        if (
            not isinstance(nodes, list)
            or not nodes
            or metadata.get("project_id") != profile.project_id
            or not isinstance(manifest, dict)
            or not manifest
        ):
            return False
        allowed = set(collect_profile_files(profile, repo_root))
        for relative, fingerprint in manifest.items():
            if relative not in allowed or not isinstance(fingerprint, str):
                return False
            if _raw_fingerprint(repo_root / relative) != fingerprint:
                return False
        node_ids = {str(node.get("id")) for node in nodes if isinstance(node, dict)}
        if len(node_ids) != len(nodes):
            return False
        if any(
            node.get("project_id") != profile.project_id
            for node in nodes
            if isinstance(node, dict)
        ):
            return False
        from fingerprints import current_source_fingerprints

        for node in nodes:
            source_name = _normalize_graphify_source(
                node.get("source_file", node.get("source_path", "")), repo_root
            )
            fingerprint = node.get("source_fingerprint")
            if (
                source_name not in allowed
                or not isinstance(fingerprint, str)
                or fingerprint
                not in current_source_fingerprints(repo_root / source_name, repo_root)
            ):
                return False
        links = existing.get("links", existing.get("edges", []))
        return isinstance(links, list) and all(
            isinstance(edge, dict)
            and str(edge.get("source")) in node_ids
            and str(edge.get("target")) in node_ids
            for edge in links
        )
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False


def publish_merged_graph(
    raw_graph_path: Path,
    target_path: Path,
    profile: GraphProfile,
    repo_root: Path,
    catalog: FactoryCatalog,
    preserve_existing: bool = False,
) -> None:
    data = json.loads(raw_graph_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("nodes"), list):
        raise ValueError("raw Graphify output has no nodes list")
    raw_edges = data.get("links", data.get("edges", []))
    if not isinstance(raw_edges, list):
        raise ValueError("raw Graphify output has no links list")

    allowed = set(collect_profile_files(profile, repo_root))
    source_fingerprints = {
        relative: _raw_fingerprint(repo_root / relative) for relative in sorted(allowed)
    }
    nodes: dict[str, dict] = {}
    source_less: dict[str, dict] = {}
    existing_links: list[dict] = []
    if preserve_existing and target_path.is_file():
        try:
            existing = json.loads(target_path.read_text(encoding="utf-8"))
            metadata = existing.get("factory_metadata", {})
            if metadata.get("project_id") == profile.project_id:
                from fingerprints import current_source_fingerprints

                for raw in existing.get("nodes", []):
                    if not isinstance(raw, dict) or not raw.get("id"):
                        continue
                    source = _normalize_graphify_source(
                        raw.get("source_file", raw.get("source_path", "")), repo_root
                    )
                    fingerprint = raw.get("source_fingerprint")
                    if (
                        source in allowed
                        and isinstance(fingerprint, str)
                        and fingerprint in current_source_fingerprints(repo_root / source, repo_root)
                    ):
                        nodes[str(raw["id"])] = dict(raw)
                old_links = existing.get("links", existing.get("edges", []))
                if isinstance(old_links, list):
                    existing_links = [edge for edge in old_links if isinstance(edge, dict)]
        except (OSError, ValueError, json.JSONDecodeError):
            nodes = {}
            existing_links = []
    for raw in data["nodes"]:
        if not isinstance(raw, dict) or not raw.get("id"):
            continue
        source = _normalize_graphify_source(
            raw.get("source_file", raw.get("source_path", "")), repo_root
        )
        if not source:
            source_less[str(raw["id"])] = dict(raw)
            continue
        if source not in allowed:
            continue
        node = dict(raw)
        node["project_id"] = profile.project_id
        node["source_file"] = source
        node["source_fingerprint"] = source_fingerprints[source]
        rule = _corpus_rule(profile, source)
        if rule is not None:
            node["source_role"] = rule.source_role
            node["stages"] = list(rule.stages)
        node.setdefault("lifecycle_state", "current")
        nodes[str(node["id"])] = node

    pending = dict(source_less)
    while pending:
        progressed = False
        for node_id, raw in list(pending.items()):
            neighbor_ids: set[str] = set()
            for edge in raw_edges:
                if not isinstance(edge, dict):
                    continue
                source_id = str(edge.get("source", ""))
                target_id = str(edge.get("target", ""))
                if source_id == node_id and target_id in nodes:
                    neighbor_ids.add(target_id)
                if target_id == node_id and source_id in nodes:
                    neighbor_ids.add(source_id)
            if not neighbor_ids:
                continue
            evidence_sources = sorted(
                {
                    str(nodes[neighbor_id]["source_file"])
                    for neighbor_id in neighbor_ids
                    if nodes[neighbor_id].get("source_file")
                }
            )
            if not evidence_sources:
                continue
            primary_source = evidence_sources[0]
            node = dict(raw)
            node.update(
                {
                    "project_id": profile.project_id,
                    "source_file": primary_source,
                    "source_fingerprint": source_fingerprints[primary_source],
                    "source_inherited": True,
                    "evidence_sources": evidence_sources,
                    "evidence_source_fingerprints": {
                        source: source_fingerprints[source]
                        for source in evidence_sources
                    },
                }
            )
            rule = _corpus_rule(profile, primary_source)
            if rule is not None:
                node["source_role"] = rule.source_role
                node["stages"] = list(rule.stages)
            node.setdefault("lifecycle_state", "current")
            nodes[node_id] = node
            del pending[node_id]
            progressed = True
        if not progressed:
            break

    for record in catalog.records:
        if not _record_is_publishable(record, profile, repo_root, allowed):
            continue
        nodes[record.node_id] = {
            "id": record.node_id,
            "label": str(
                record.properties.get("value")
                or record.properties.get("label")
                or record.properties.get("artifact_kind")
                or record.node_id
            ),
            "summary": str(record.properties.get("summary") or record.properties),
            "file_type": record.node_type,
            "type": record.node_type,
            "source_file": record.source_path,
            "source_fingerprint": record.source_fingerprint
            or source_fingerprints[record.source_path],
            "project_id": profile.project_id,
            "provenance": "EXTRACTED",
            "confidence_score": 1.0,
            "properties": record.properties,
        }
        for field in (
            "source_locator",
            "source_span",
            "file_sha256",
            "slice_sha256",
            "source_role",
            "routes",
            "stages",
            "lifecycle_state",
        ):
            value = record.properties.get(field)
            if value is not None:
                nodes[record.node_id][field] = value
        rule = _corpus_rule(profile, record.source_path)
        if rule is not None:
            nodes[record.node_id].setdefault("source_role", rule.source_role)
            nodes[record.node_id].setdefault("stages", list(rule.stages))
        nodes[record.node_id].setdefault("lifecycle_state", "current")
        source_location = record.properties.get("source_location")
        if isinstance(source_location, str) and source_location.strip():
            nodes[record.node_id]["source_location"] = source_location.strip()

    links = []
    for edge in existing_links:
        if str(edge.get("source")) in nodes and str(edge.get("target")) in nodes:
            links.append(dict(edge))
    for edge in raw_edges:
        if not isinstance(edge, dict):
            continue
        if str(edge.get("source")) in nodes and str(edge.get("target")) in nodes:
            links.append(dict(edge))
    for edge in catalog.relationships:
        if edge.source_id in nodes and edge.target_id in nodes:
            source_node = nodes[edge.source_id]
            links.append(
                {
                    "source": edge.source_id,
                    "target": edge.target_id,
                    "relation": edge.relation_type,
                    "context": edge.relation_type,
                    "confidence": edge.provenance,
                    "confidence_score": edge.confidence,
                    "source_file": source_node.get("source_file", ""),
                    "source_location": source_node.get("source_location", ""),
                }
            )

    if not nodes:
        raise ValueError("merged graph is empty")
    node_ids = set(nodes)
    required_catalog_ids = {
        record.node_id
        for record in catalog.records
        if _record_is_publishable(record, profile, repo_root, allowed)
    }
    if not required_catalog_ids.issubset(node_ids):
        raise ValueError("merged graph is missing required catalog coverage")
    if any(
        str(edge.get("source", "")) not in node_ids
        or str(edge.get("target", "")) not in node_ids
        for edge in links
    ):
        raise ValueError("merged graph has dangling relationships")

    output = {
        key: value
        for key, value in data.items()
        if key not in {"nodes", "links", "edges", "factory_metadata"}
    }
    output["nodes"] = sorted(nodes.values(), key=lambda node: str(node["id"]))
    unique_links = {
        (
            str(edge.get("source")),
            str(edge.get("target")),
            str(edge.get("relation", "")),
            str(edge.get("context", "")),
        ): edge
        for edge in links
    }
    output["links"] = sorted(
        unique_links.values(),
        key=lambda edge: (
            str(edge.get("source")),
            str(edge.get("relation", "")),
            str(edge.get("target")),
        ),
    )
    output["factory_metadata"] = {
        "schema_version": "1.1",
        "project_id": profile.project_id,
        "source_fingerprints": source_fingerprints,
    }
    output["directed"] = True
    output["multigraph"] = True
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = target_path.with_suffix(target_path.suffix + ".tmp")
    temporary.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(target_path)
