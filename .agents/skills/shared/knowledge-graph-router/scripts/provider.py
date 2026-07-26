from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from graph_profile import GraphProfile


@dataclass(frozen=True)
class GraphRecord:
    node_id: str
    project_id: str
    node_type: str
    source_path: str
    source_fingerprint: str | None
    properties: dict[str, object]


@dataclass(frozen=True)
class GraphRelationship:
    source_id: str
    target_id: str
    relation_type: str
    provenance: str
    confidence: float


@dataclass(frozen=True)
class FactoryCatalog:
    records: tuple[GraphRecord, ...]
    relationships: tuple[GraphRelationship, ...]


@dataclass(frozen=True)
class GraphQuery:
    project_id: str
    stage: str
    question: str
    route: str | None = None
    entity_ids: tuple[str, ...] = ()
    allowed_provenance: tuple[str, ...] = ("EXTRACTED", "INFERRED")
    token_budget: int = 1200


@dataclass(frozen=True)
class GraphContextHit:
    node_id: str
    project_id: str
    node_type: str
    summary: str
    source_path: str
    source_location: str | None
    source_fingerprint: str | None
    provenance: str
    confidence: float
    evidence_path: tuple[str, ...]


@dataclass(frozen=True)
class GraphHealth:
    available: bool
    fresh: bool
    node_count: int
    edge_count: int
    stale_sources: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class ContextRequest:
    query: GraphQuery
    filesystem_allowlist: tuple[str, ...]
    require_exact_types: tuple[str, ...] = (
        "Claim",
        "Approval",
        "Conflict",
        "ReleaseEvidence",
    )


@dataclass(frozen=True)
class ContextResult:
    hits: tuple[GraphContextHit, ...]
    loaded_files: tuple[str, ...]
    used_fallback: bool
    fallback_reason: str | None
    estimated_tokens: int


class KnowledgeGraphProvider(Protocol):
    def update(
        self, profile: GraphProfile, repo_root: Path, incremental: bool = True
    ) -> GraphHealth: ...

    def query(self, request: GraphQuery) -> list[GraphContextHit]: ...

    def health(self, profile: GraphProfile) -> GraphHealth: ...

    def explain(self, node_id: str) -> tuple[str, ...]: ...
