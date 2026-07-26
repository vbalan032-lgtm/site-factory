from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import subprocess

from graph_profile import GraphProfile, resolve_repo_path
from fingerprints import current_source_fingerprints
from provider import GraphContextHit, GraphHealth, GraphQuery


PROVENANCE_ORDER = {"EXTRACTED": 0, "INFERRED": 1, "AMBIGUOUS": 2}
CONFIDENCE_SCORES = {"EXTRACTED": 1.0, "INFERRED": 0.7, "AMBIGUOUS": 0.3}


def _query_terms(value: str) -> set[str]:
    return {term for term in re.findall(r"[\w-]+", value.lower()) if len(term) >= 2}


def _search_text(node: dict) -> str:
    values = [
        node.get("id"),
        node.get("label"),
        node.get("summary"),
        node.get("type"),
        node.get("node_type"),
        node.get("source_path"),
        node.get("route"),
    ]
    properties = node.get("properties")
    if isinstance(properties, dict):
        values.extend(properties.values())
    return " ".join(str(value) for value in values if value is not None).lower()


class GraphifyJsonProvider:
    def __init__(
        self,
        profile: GraphProfile,
        repo_root: Path,
        graphify_command: str = "graphify",
        command_runner=subprocess.run,
    ) -> None:
        self.profile = profile
        self.repo_root = repo_root.resolve()
        self.graphify_command = graphify_command
        self.command_runner = command_runner
        self.graph_path = (self.repo_root / profile.output_path).resolve()
        self.graph_path.relative_to(self.repo_root)

    def _read_graph(self) -> dict:
        data = json.loads(self.graph_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("nodes"), list):
            raise ValueError("graph JSON must contain a nodes list")
        edges = data.get("edges", data.get("links", []))
        if not isinstance(edges, list):
            raise ValueError("graph JSON edges must be a list")
        metadata = data.get("factory_metadata", {})
        if not isinstance(metadata, dict):
            raise ValueError("factory_metadata must be an object")
        graph_project = metadata.get("project_id")
        node_projects = {
            node.get("project_id")
            for node in data["nodes"]
            if isinstance(node, dict) and node.get("project_id")
        }
        if graph_project is None and node_projects == {self.profile.project_id}:
            graph_project = self.profile.project_id
        if graph_project != self.profile.project_id:
            raise ValueError("graph project manifest does not match profile")
        fingerprints = metadata.get("source_fingerprints", {})
        if not isinstance(fingerprints, dict):
            fingerprints = {}

        adjacent: dict[str, list[tuple[str, float, str]]] = {}
        for edge in edges:
            if not isinstance(edge, dict):
                continue
            source = str(edge.get("source", ""))
            target = str(edge.get("target", ""))
            provenance = str(edge.get("confidence", edge.get("provenance", "EXTRACTED")))
            score = edge.get("confidence_score", CONFIDENCE_SCORES.get(provenance, 0.0))
            try:
                numeric_score = float(score)
            except (TypeError, ValueError):
                numeric_score = CONFIDENCE_SCORES.get(provenance, 0.0)
            adjacent.setdefault(source, []).append((provenance, numeric_score, target))
            adjacent.setdefault(target, []).append((provenance, numeric_score, source))

        normalized_nodes = []
        for raw in data["nodes"]:
            if not isinstance(raw, dict):
                continue
            node = dict(raw)
            node_id = str(node.get("id", ""))
            source_path = node.get("source_path", node.get("source_file", ""))
            edge_evidence = sorted(
                adjacent.get(node_id, []),
                key=lambda item: (PROVENANCE_ORDER.get(item[0], 99), -item[1], item[2]),
            )
            provenance = node.get("provenance")
            if provenance is None and isinstance(node.get("confidence"), str):
                provenance = node.get("confidence")
            if provenance is None:
                provenance = edge_evidence[0][0] if edge_evidence else "EXTRACTED"
            confidence = node.get("confidence_score")
            if confidence is None and isinstance(node.get("confidence"), (int, float)):
                confidence = node.get("confidence")
            if confidence is None:
                confidence = edge_evidence[0][1] if edge_evidence else CONFIDENCE_SCORES.get(str(provenance), 0.0)
            properties = node.get("properties")
            node.update(
                {
                    "project_id": node.get("project_id", graph_project),
                    "source_path": str(source_path or ""),
                    "source_fingerprint": node.get(
                        "source_fingerprint", fingerprints.get(str(source_path or ""))
                    ),
                    "type": node.get("type", node.get("node_type", node.get("file_type", "Entity"))),
                    "summary": node.get("summary", node.get("label", "")),
                    "provenance": str(provenance),
                    "confidence_score": float(confidence),
                    "evidence_path": list(
                        dict.fromkeys(
                            list(node.get("evidence_path", [item[2] for item in edge_evidence]))
                            + list(node.get("evidence_sources", []))
                        )
                    ),
                    "source_locator": node.get(
                        "source_locator",
                        properties.get("source_locator") if isinstance(properties, dict) else None,
                    ),
                    "source_span": node.get(
                        "source_span",
                        properties.get("source_span") if isinstance(properties, dict) else None,
                    ),
                    "source_role": node.get(
                        "source_role",
                        properties.get("source_role", "canonical")
                        if isinstance(properties, dict)
                        else "canonical",
                    ),
                    "lifecycle_state": node.get(
                        "lifecycle_state",
                        properties.get("lifecycle_state", "current")
                        if isinstance(properties, dict)
                        else "current",
                    ),
                }
            )
            normalized_nodes.append(node)
        data["nodes"] = normalized_nodes
        data["edges"] = edges
        return data

    def health(self, profile: GraphProfile) -> GraphHealth:
        if profile.project_id != self.profile.project_id:
            return GraphHealth(
                False,
                False,
                0,
                0,
                (),
                ("project isolation mismatch",),
                state="unavailable",
            )
        try:
            data = self._read_graph()
            age_minutes = (
                datetime.now(timezone.utc).timestamp() - self.graph_path.stat().st_mtime
            ) / 60
            changed: set[str] = set()
            affected: set[str] = set()
            warnings: list[str] = []
            metadata = data.get("factory_metadata", {})
            manifest = metadata.get("source_fingerprints", {}) if isinstance(metadata, dict) else {}
            if isinstance(manifest, dict):
                from graph_update import collect_profile_files

                current_corpus = set(collect_profile_files(profile, self.repo_root))
                manifest_paths = {
                    path for path in manifest if isinstance(path, str)
                }
                changed.update(current_corpus.symmetric_difference(manifest_paths))
                if len(manifest_paths) != len(manifest):
                    warnings.append("malformed graph source manifest")
                for source_path, fingerprint in manifest.items():
                    if not isinstance(source_path, str) or not isinstance(fingerprint, str):
                        warnings.append("malformed graph source manifest")
                        continue
                    try:
                        normalized, source = resolve_repo_path(
                            source_path, "graph manifest", self.repo_root
                        )
                    except ValueError:
                        changed.add(source_path)
                        warnings.append("unsafe graph manifest path")
                        continue
                    if not source.is_file():
                        changed.add(normalized)
                        continue
                    if fingerprint not in current_source_fingerprints(source, self.repo_root):
                        changed.add(normalized)
            else:
                warnings.append("malformed graph source manifest")
            for node in data["nodes"]:
                if not isinstance(node, dict):
                    warnings.append("invalid graph node")
                    continue
                if node.get("project_id") not in {None, profile.project_id}:
                    warnings.append("cross-project node excluded")
                source_path = node.get("source_path")
                fingerprint = node.get("source_fingerprint")
                if isinstance(source_path, str) and isinstance(fingerprint, str):
                    try:
                        normalized, source = resolve_repo_path(
                            source_path, "graph node", self.repo_root
                        )
                    except ValueError:
                        changed.add(source_path)
                        affected.add(str(node.get("id", "")))
                        warnings.append("unsafe graph node path")
                        continue
                    if not source.is_file():
                        changed.add(normalized)
                        affected.add(str(node.get("id", "")))
                    else:
                        actual = current_source_fingerprints(source, self.repo_root)
                        if fingerprint not in actual:
                            changed.add(normalized)
                            affected.add(str(node.get("id", "")))
                elif isinstance(source_path, str) and source_path in changed:
                    affected.add(str(node.get("id", "")))
            for node in data["nodes"]:
                if isinstance(node, dict) and str(node.get("source_path", "")) in changed:
                    affected.add(str(node.get("id", "")))
            if age_minutes > profile.freshness_max_age_minutes:
                warnings.append("graph age exceeds freshness policy; fingerprints remain authoritative")
            degraded = bool(changed) or any(
                warning
                for warning in warnings
                if "age exceeds" not in warning
            )
            fresh = not degraded
            return GraphHealth(
                True,
                fresh,
                len(data["nodes"]),
                len(data["edges"]),
                tuple(sorted(changed)),
                tuple(sorted(set(warnings))),
                state="degraded" if degraded else "current",
                changed_sources=tuple(sorted(changed)),
                affected_node_ids=tuple(sorted(node_id for node_id in affected if node_id)),
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return GraphHealth(
                False,
                False,
                0,
                0,
                (),
                (f"graph unavailable: {exc}",),
                state="unavailable",
            )

    def query(self, request: GraphQuery) -> list[GraphContextHit]:
        if request.project_id != self.profile.project_id:
            raise ValueError("query project_id does not match graph profile")
        stage_budget = self.profile.stage_budgets.get(request.stage)
        if not isinstance(stage_budget, int) or stage_budget <= 0:
            raise ValueError("query stage has no configured token budget")
        stage_limit = self.profile.stage_limits.get(request.stage)
        summary_budget = (
            stage_limit.summary_tokens if stage_limit is not None else stage_budget
        )
        top_k = stage_limit.top_k if stage_limit is not None else 12
        effective_budget = min(request.token_budget, stage_budget, summary_budget)
        data = self._read_graph()
        allowed = set(request.allowed_provenance)
        terms = _query_terms(request.question)
        allowed_roles = set(request.allowed_source_roles)

        def string_tuple(value: object) -> tuple[str, ...]:
            if isinstance(value, list):
                return tuple(str(item) for item in value if isinstance(item, str))
            if isinstance(value, tuple):
                return tuple(str(item) for item in value if isinstance(item, str))
            return ()

        def eligible(node: dict, require_terms: bool = True) -> bool:
            if node.get("project_id") != request.project_id:
                return False
            search_text = _search_text(node)
            if require_terms and terms and not any(term in search_text for term in terms):
                return False
            node_route = node.get("route")
            properties = node.get("properties")
            if node_route is None and isinstance(properties, dict):
                node_route = properties.get("route")
            node_routes = string_tuple(
                node.get("routes", properties.get("routes", []))
                if isinstance(properties, dict)
                else node.get("routes", [])
            )
            if request.route is not None:
                if (node_route or node_routes) and node_route != request.route and request.route not in node_routes:
                    return False
            node_stages = string_tuple(
                node.get("stages", properties.get("stages", []))
                if isinstance(properties, dict)
                else node.get("stages", [])
            )
            if node_stages and request.stage not in node_stages:
                return False
            if str(node.get("type", "")) == "Stage" and isinstance(properties, dict):
                value = properties.get("value")
                if isinstance(value, str) and value != request.stage:
                    return False
            if request.entity_ids:
                evidence = node.get("evidence_path", [])
                linked = {str(node.get("id", ""))}
                if isinstance(evidence, list):
                    linked.update(str(item) for item in evidence)
                if not linked.intersection(request.entity_ids):
                    return False
            provenance = str(node.get("provenance", "AMBIGUOUS"))
            if provenance not in allowed:
                return False
            source_role = str(node.get("source_role", "canonical"))
            if source_role not in allowed_roles:
                return False
            lifecycle = str(node.get("lifecycle_state", "current"))
            if lifecycle in {"excluded", "changed_dependency"}:
                return False
            if lifecycle == "migration_evidence" and not request.include_migration_evidence:
                return False
            return True

        def score(node: dict) -> tuple[float, tuple[str, ...]]:
            search_text = _search_text(node)
            matched = tuple(sorted(term for term in terms if term in search_text))
            coverage = len(matched) / len(terms) if terms else 1.0
            phrase = request.question.strip().casefold()
            phrase_bonus = 0.5 if phrase and phrase in search_text else 0.0
            provenance = str(node.get("provenance", "AMBIGUOUS"))
            provenance_bonus = {"EXTRACTED": 0.2, "INFERRED": 0.1}.get(provenance, 0.0)
            confidence = float(node.get("confidence_score", 0.0))
            return round(coverage + phrase_bonus + provenance_bonus + confidence * 0.1, 6), matched

        def to_hit(node: dict, relevance: float, matched: tuple[str, ...]) -> GraphContextHit:
            properties = node.get("properties")
            summary = str(node.get("summary", node.get("label", ""))).strip()
            evidence = node.get("evidence_path", [])
            if not isinstance(evidence, list):
                evidence = []
            raw_span = node.get("source_span")
            source_span = None
            if (
                isinstance(raw_span, (list, tuple))
                and len(raw_span) == 2
                and all(isinstance(value, int) for value in raw_span)
            ):
                source_span = (int(raw_span[0]), int(raw_span[1]))
            return GraphContextHit(
                node_id=str(node.get("id", "")),
                project_id=request.project_id,
                node_type=str(node.get("type", node.get("node_type", "Entity"))),
                summary=summary,
                source_path=str(node.get("source_path", "")),
                source_location=node.get("source_location"),
                source_fingerprint=node.get("source_fingerprint"),
                provenance=str(node.get("provenance", "AMBIGUOUS")),
                confidence=float(node.get("confidence_score", 0.0)),
                evidence_path=tuple(str(item) for item in evidence),
                relevance_score=relevance,
                matched_terms=matched,
                source_role=str(node.get("source_role", "canonical")),
                lifecycle_state=str(node.get("lifecycle_state", "current")),
                source_locator=node.get("source_locator"),
                source_span=source_span,
                file_sha256=node.get("file_sha256"),
                slice_sha256=node.get("slice_sha256"),
                routes=string_tuple(
                    node.get("routes", properties.get("routes", []))
                    if isinstance(properties, dict)
                    else node.get("routes", [])
                ),
                stages=string_tuple(
                    node.get("stages", properties.get("stages", []))
                    if isinstance(properties, dict)
                    else node.get("stages", [])
                ),
            )

        nodes_by_id = {
            str(node.get("id")): node
            for node in data["nodes"]
            if isinstance(node, dict) and node.get("id")
        }
        adjacent: dict[str, list[str]] = {}
        for edge in data["edges"]:
            if not isinstance(edge, dict):
                continue
            relation = str(edge.get("relation", ""))
            if not relation or relation != relation.upper():
                continue
            source = str(edge.get("source", ""))
            target = str(edge.get("target", ""))
            adjacent.setdefault(source, []).append(target)
            adjacent.setdefault(target, []).append(source)
        ranked = []
        for node in nodes_by_id.values():
            if eligible(node):
                relevance, matched = score(node)
                ranked.append((relevance, matched, node))
        ranked.sort(
            key=lambda item: (
                -item[0],
                PROVENANCE_ORDER.get(str(item[2].get("provenance")), 99),
                str(item[2].get("id", "")),
            )
        )

        ordered: list[tuple[dict, float, tuple[str, ...]]] = []
        seen: set[str] = set()
        for relevance, matched, node in ranked:
            node_id = str(node.get("id", ""))
            if node_id not in seen:
                ordered.append((node, relevance, matched))
                seen.add(node_id)
            for dependency_id in sorted(set(adjacent.get(node_id, []))):
                dependency = nodes_by_id.get(dependency_id)
                if dependency is None or dependency_id in seen or not eligible(dependency, require_terms=False):
                    continue
                dependency_score, dependency_terms = score(dependency)
                ordered.append((dependency, dependency_score * 0.5, dependency_terms))
                seen.add(dependency_id)

        hits: list[GraphContextHit] = []
        used_tokens = 0
        for node, relevance, matched in ordered:
            hit = to_hit(node, relevance, matched)
            estimate = max(1, (len(hit.summary) + 3) // 4)
            if used_tokens + estimate > effective_budget:
                continue
            hits.append(hit)
            used_tokens += estimate
            if len(hits) >= top_k:
                break
        return hits

    def update(
        self, profile: GraphProfile, repo_root: Path, incremental: bool = True
    ) -> GraphHealth:
        resolved_root = repo_root.resolve()
        if resolved_root != self.repo_root or profile != self.profile:
            return GraphHealth(False, False, 0, 0, (), ("unsafe update scope",))
        from factory_catalog import build_factory_catalog
        from graph_update import materialize_profile_corpus, publish_merged_graph

        try:
            staging, included = materialize_profile_corpus(profile, self.repo_root)
        except OSError as exc:
            return GraphHealth(False, False, 0, 0, (), (f"corpus staging failed: {exc}",))
        if not included:
            return GraphHealth(False, False, 0, 0, (), ("profile corpus is empty",))
        run_root = self.repo_root / "graphify-out/.provider-run"
        if not incremental and run_root.exists():
            shutil.rmtree(run_root)
        command = [
            self.graphify_command,
            "extract",
            str(staging),
            "--out",
            str(run_root),
            "--no-cluster",
        ]
        if profile.extraction_mode == "code-only":
            command.append("--code-only")
        try:
            completed = self.command_runner(
                command,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
        except OSError as exc:
            return GraphHealth(False, False, 0, 0, (), (f"graphify CLI unavailable: {exc}",))
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()
            if len(detail) > 600:
                detail = detail[-600:]
            suffix = f": {detail}" if detail else ""
            return GraphHealth(
                False,
                False,
                0,
                0,
                (),
                (f"graphify update failed with exit code {completed.returncode}{suffix}",),
            )
        raw_graph = run_root / "graphify-out/graph.json"
        try:
            catalog = build_factory_catalog(profile, self.repo_root)
            publish_merged_graph(
                raw_graph,
                self.graph_path,
                profile,
                self.repo_root,
                catalog,
                preserve_existing=incremental,
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return GraphHealth(
                False,
                False,
                0,
                0,
                (),
                (f"graph merge failed; previous graph preserved: {exc}",),
            )
        return self.health(profile)

    def explain(self, node_id: str) -> tuple[str, ...]:
        data = self._read_graph()
        for node in data["nodes"]:
            if isinstance(node, dict) and str(node.get("id")) == node_id:
                evidence = node.get("evidence_path", [])
                return tuple(str(item) for item in evidence) if isinstance(evidence, list) else ()
        return ()
