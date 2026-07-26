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
    return {term for term in re.findall(r"[\w-]+", value.lower()) if len(term) >= 3}


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
                }
            )
            normalized_nodes.append(node)
        data["nodes"] = normalized_nodes
        data["edges"] = edges
        return data

    def health(self, profile: GraphProfile) -> GraphHealth:
        if profile.project_id != self.profile.project_id:
            return GraphHealth(False, False, 0, 0, (), ("project isolation mismatch",))
        try:
            data = self._read_graph()
            age_minutes = (
                datetime.now(timezone.utc).timestamp() - self.graph_path.stat().st_mtime
            ) / 60
            stale: set[str] = set()
            warnings: list[str] = []
            metadata = data.get("factory_metadata", {})
            manifest = metadata.get("source_fingerprints", {}) if isinstance(metadata, dict) else {}
            if isinstance(manifest, dict):
                from graph_update import collect_profile_files

                current_corpus = set(collect_profile_files(profile, self.repo_root))
                manifest_paths = {
                    path for path in manifest if isinstance(path, str)
                }
                stale.update(current_corpus.symmetric_difference(manifest_paths))
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
                        stale.add(source_path)
                        warnings.append("unsafe graph manifest path")
                        continue
                    if not source.is_file():
                        stale.add(normalized)
                        continue
                    if fingerprint not in current_source_fingerprints(source, self.repo_root):
                        stale.add(normalized)
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
                        stale.add(source_path)
                        warnings.append("unsafe graph node path")
                        continue
                    if not source.is_file():
                        stale.add(normalized)
                    else:
                        actual = current_source_fingerprints(source, self.repo_root)
                        if fingerprint not in actual:
                            stale.add(normalized)
            fresh = (
                age_minutes <= profile.freshness_max_age_minutes
                and not stale
                and "malformed graph source manifest" not in warnings
            )
            if age_minutes > profile.freshness_max_age_minutes:
                warnings.append("graph exceeds freshness policy")
            return GraphHealth(
                True,
                fresh,
                len(data["nodes"]),
                len(data["edges"]),
                tuple(sorted(stale)),
                tuple(sorted(set(warnings))),
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return GraphHealth(False, False, 0, 0, (), (f"graph unavailable: {exc}",))

    def query(self, request: GraphQuery) -> list[GraphContextHit]:
        if request.project_id != self.profile.project_id:
            raise ValueError("query project_id does not match graph profile")
        stage_budget = self.profile.stage_budgets.get(request.stage)
        if not isinstance(stage_budget, int) or stage_budget <= 0:
            raise ValueError("query stage has no configured token budget")
        effective_budget = min(request.token_budget, stage_budget)
        data = self._read_graph()
        allowed = set(request.allowed_provenance)
        terms = _query_terms(request.question)
        hits: list[GraphContextHit] = []
        used_tokens = 0
        for node in sorted(
            (item for item in data["nodes"] if isinstance(item, dict)),
            key=lambda item: (
                PROVENANCE_ORDER.get(str(item.get("provenance")), 99),
                -float(item.get("confidence", 0.0)),
                str(item.get("id", "")),
            ),
        ):
            if node.get("project_id") != request.project_id:
                continue
            if terms and not any(term in _search_text(node) for term in terms):
                continue
            node_route = node.get("route")
            properties = node.get("properties")
            if node_route is None and isinstance(properties, dict):
                node_route = properties.get("route")
            if request.route is not None:
                node_routes = properties.get("routes", []) if isinstance(properties, dict) else []
                if node_route != request.route and request.route not in node_routes:
                    continue
            if request.entity_ids:
                evidence = node.get("evidence_path", [])
                linked = {str(node.get("id", ""))}
                if isinstance(evidence, list):
                    linked.update(str(item) for item in evidence)
                if not linked.intersection(request.entity_ids):
                    continue
            provenance = str(node.get("provenance", "AMBIGUOUS"))
            if provenance not in allowed:
                continue
            summary = str(node.get("summary", node.get("label", ""))).strip()
            estimate = max(1, (len(summary) + 3) // 4)
            if used_tokens + estimate > effective_budget:
                continue
            used_tokens += estimate
            evidence = node.get("evidence_path", [])
            if not isinstance(evidence, list):
                evidence = []
            hits.append(
                GraphContextHit(
                    node_id=str(node.get("id", "")),
                    project_id=request.project_id,
                    node_type=str(node.get("type", node.get("node_type", "Entity"))),
                    summary=summary,
                    source_path=str(node.get("source_path", "")),
                    source_location=node.get("source_location"),
                    source_fingerprint=node.get("source_fingerprint"),
                    provenance=provenance,
                    confidence=float(node.get("confidence_score", node.get("confidence", 0.0))),
                    evidence_path=tuple(str(item) for item in evidence),
                )
            )
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
