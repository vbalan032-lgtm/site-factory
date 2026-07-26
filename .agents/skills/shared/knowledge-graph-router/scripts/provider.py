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
    allowed_source_roles: tuple[str, ...] = (
        "canonical",
        "design",
        "page_artifact",
        "implementation",
        "lifecycle",
    )
    include_migration_evidence: bool = False


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
    relevance_score: float = 0.0
    matched_terms: tuple[str, ...] = ()
    source_role: str = "canonical"
    lifecycle_state: str = "current"
    source_locator: str | None = None
    source_span: tuple[int, int] | None = None
    file_sha256: str | None = None
    slice_sha256: str | None = None
    routes: tuple[str, ...] = ()
    stages: tuple[str, ...] = ()


@dataclass(frozen=True)
class GraphHealth:
    available: bool
    fresh: bool
    node_count: int
    edge_count: int
    stale_sources: tuple[str, ...]
    warnings: tuple[str, ...]
    state: str | None = None
    changed_sources: tuple[str, ...] = ()
    affected_node_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.state is None:
            state = "unavailable" if not self.available else "current" if self.fresh else "degraded"
            object.__setattr__(self, "state", state)
        if not self.changed_sources and self.stale_sources:
            object.__setattr__(self, "changed_sources", self.stale_sources)


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
class ExactEvidenceSlice:
    node_id: str
    source_path: str
    source_locator: str
    source_span: tuple[int, int]
    text: str
    file_sha256: str
    slice_sha256: str
    reason: str


@dataclass(frozen=True)
class ExcludedContextHit:
    node_id: str
    source_path: str
    reason: str


@dataclass(frozen=True)
class SourceReadTrigger:
    source_path: str
    reason: str


@dataclass(frozen=True)
class BudgetBreakdown:
    summary_tokens: int
    exact_tokens: int
    full_file_tokens: int
    total_tokens: int
    summary_limit: int
    exact_limit: int
    total_limit: int
    top_k: int


@dataclass(frozen=True)
class ContextResult:
    hits: tuple[GraphContextHit, ...]
    loaded_files: tuple[str, ...]
    used_fallback: bool
    fallback_reason: str | None
    estimated_tokens: int
    summaries: tuple[GraphContextHit, ...] = ()
    exact_slices: tuple[ExactEvidenceSlice, ...] = ()
    excluded_hits: tuple[ExcludedContextHit, ...] = ()
    budget_breakdown: BudgetBreakdown | None = None
    full_file_fallback_reasons: tuple[str, ...] = ()
    exact_source_triggers: tuple[SourceReadTrigger, ...] = ()
    graph_health: GraphHealth | None = None

    def __post_init__(self) -> None:
        if not self.summaries and self.hits:
            object.__setattr__(self, "summaries", self.hits)


class KnowledgeGraphProvider(Protocol):
    def update(
        self, profile: GraphProfile, repo_root: Path, incremental: bool = True
    ) -> GraphHealth: ...

    def query(self, request: GraphQuery) -> list[GraphContextHit]: ...

    def health(self, profile: GraphProfile) -> GraphHealth: ...

    def explain(self, node_id: str) -> tuple[str, ...]: ...
