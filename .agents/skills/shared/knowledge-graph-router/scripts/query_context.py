from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path, PurePosixPath
import re
import sys

from fingerprints import current_source_fingerprints
from provider import (
    BudgetBreakdown,
    ContextRequest,
    ContextResult,
    ExactEvidenceSlice,
    ExcludedContextHit,
    GraphContextHit,
    GraphQuery,
    KnowledgeGraphProvider,
    SourceReadTrigger,
)
from source_resolver import resolve_source_slice

SENSITIVE_INTENT = re.compile(
    r"(?:claim|proof|approval|conflict|release|production|СѓС‚РІРµСЂР¶РґРµРЅ|РґРѕРєР°Р·|СЃРѕРіР»Р°СЃРѕРІР°РЅ|РєРѕРЅС„Р»РёРєС‚|СЃРїРѕСЂ|СЂРµР»РёР·)",
    re.IGNORECASE,
)


def _safe_relative(value: str, repo_root: Path) -> tuple[str, Path] | None:
    pure = PurePosixPath(value.replace("\\", "/"))
    if pure.is_absolute() or any(part == ".." for part in pure.parts):
        return None
    path = (repo_root / Path(*pure.parts)).resolve()
    try:
        path.relative_to(repo_root.resolve())
    except ValueError:
        return None
    return pure.as_posix(), path


def _filesystem_files(
    allowlist: tuple[str, ...], repo_root: Path
) -> tuple[tuple[str, ...], int]:
    loaded: list[str] = []
    characters = 0
    for value in allowlist:
        resolved = _safe_relative(value, repo_root)
        if resolved is None:
            continue
        relative, path = resolved
        if not path.is_file():
            continue
        try:
            characters += len(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
        loaded.append(relative)
    return tuple(dict.fromkeys(loaded)), max(0, (characters + 3) // 4)


def _limits(request: ContextRequest, profile: object) -> tuple[int, int, int, int]:
    stage = request.query.stage
    stage_budgets = getattr(profile, "stage_budgets", {})
    total = stage_budgets.get(stage)
    if not isinstance(total, int) or total <= 0:
        total = max(1, request.query.token_budget)
    total = min(total, request.query.token_budget)
    limits = getattr(profile, "stage_limits", {})
    limit = limits.get(stage) if isinstance(limits, dict) else None
    if limit is None:
        return total, total, total, 12
    return (
        min(total, int(limit.summary_tokens)),
        min(total, int(limit.exact_tokens)),
        min(total, int(limit.total_tokens)),
        int(limit.top_k),
    )


def _fallback(
    request: ContextRequest,
    repo_root: Path,
    reason: str,
    profile: object | None = None,
    health: object | None = None,
) -> ContextResult:
    files, tokens = _filesystem_files(request.filesystem_allowlist, repo_root)
    summary_limit, exact_limit, total_limit, top_k = _limits(
        request, profile or object()
    )
    budget = BudgetBreakdown(
        0,
        0,
        tokens,
        tokens,
        summary_limit,
        exact_limit,
        total_limit,
        top_k,
    )
    return ContextResult(
        (),
        files,
        True,
        reason,
        tokens,
        budget_breakdown=budget,
        full_file_fallback_reasons=(reason,),
        exact_source_triggers=tuple(SourceReadTrigger(path, reason) for path in files),
        graph_health=health,
    )


def route_context(
    request: ContextRequest,
    provider: KnowledgeGraphProvider,
    repo_root: Path,
) -> ContextResult:
    profile = getattr(provider, "profile", None)
    stage_budgets = getattr(profile, "stage_budgets", {})
    stage_budget = stage_budgets.get(request.query.stage)
    if not isinstance(stage_budget, int) or stage_budget <= 0:
        return _fallback(request, repo_root, "stage budget unavailable", profile)
    summary_limit, exact_limit, total_limit, top_k = _limits(request, profile)
    effective_budget = min(request.query.token_budget, stage_budget)
    effective_query = replace(request.query, token_budget=effective_budget)
    try:
        health = provider.health(profile)
    except Exception as exc:  # provider boundary must preserve filesystem operation
        return _fallback(request, repo_root, f"graph unavailable: {exc}", profile)
    if not health.available:
        return _fallback(request, repo_root, "graph unavailable", profile, health)

    try:
        candidate_hits = provider.query(effective_query)
    except Exception as exc:
        return _fallback(
            request, repo_root, f"graph query unavailable: {exc}", profile, health
        )
    if any(hit.project_id != effective_query.project_id for hit in candidate_hits):
        return _fallback(
            request,
            repo_root,
            "cross-project graph result rejected",
            profile,
            health,
        )

    allowed_files = set(request.filesystem_allowlist)
    accepted: list[GraphContextHit] = []
    exact_slices: list[ExactEvidenceSlice] = []
    excluded: list[ExcludedContextHit] = []
    full_files: list[str] = []
    full_file_reasons: list[str] = []
    source_triggers: list[SourceReadTrigger] = []
    exact_blocked = False
    sensitive_intent = bool(SENSITIVE_INTENT.search(effective_query.question))
    summary_tokens = 0
    exact_tokens = 0
    affected_ids = set(getattr(health, "affected_node_ids", ()))
    changed_sources = set(
        getattr(health, "changed_sources", getattr(health, "stale_sources", ()))
    )

    def add_full_file(relative: str, reason: str) -> None:
        if relative in allowed_files:
            full_files.append(relative)
            full_file_reasons.append(reason)
            source_triggers.append(SourceReadTrigger(relative, reason))

    def add_exact_slice(hit: GraphContextHit, relative: str, path: Path, reason: str) -> bool:
        nonlocal exact_tokens
        locator = hit.source_locator
        if not isinstance(locator, str) or not locator.strip():
            add_full_file(relative, "unresolved_locator")
            return False
        try:
            resolved_slice = resolve_source_slice(path, locator)
        except (OSError, UnicodeDecodeError, ValueError):
            add_full_file(relative, "unresolved_locator")
            return False
        estimate = max(1, (len(resolved_slice.text) + 3) // 4)
        if exact_tokens + estimate > exact_limit:
            excluded.append(
                ExcludedContextHit(hit.node_id, relative, "exact_budget_exceeded")
            )
            return False
        exact_tokens += estimate
        exact_slices.append(
            ExactEvidenceSlice(
                node_id=hit.node_id,
                source_path=relative,
                source_locator=resolved_slice.source_locator,
                source_span=resolved_slice.source_span,
                text=resolved_slice.text,
                file_sha256=resolved_slice.file_sha256,
                slice_sha256=resolved_slice.slice_sha256,
                reason=reason,
            )
        )
        return True

    for hit in candidate_hits:
        if hit.lifecycle_state in {"excluded", "migration_evidence", "changed_dependency"}:
            excluded.append(
                ExcludedContextHit(hit.node_id, hit.source_path, hit.lifecycle_state)
            )
            continue
        resolved = _safe_relative(hit.source_path, repo_root)
        if resolved is None:
            excluded.append(
                ExcludedContextHit(hit.node_id, hit.source_path, "unsafe_source_path")
            )
            continue
        relative, path = resolved
        if not path.is_file():
            excluded.append(
                ExcludedContextHit(hit.node_id, relative, "missing_source")
            )
            continue
        is_affected = hit.node_id in affected_ids or relative in changed_sources
        fingerprint_current = False
        if hit.source_fingerprint:
            try:
                fingerprint_current = hit.source_fingerprint in current_source_fingerprints(
                    path, repo_root
                )
            except OSError:
                fingerprint_current = False
        if is_affected or not fingerprint_current:
            excluded.append(
                ExcludedContextHit(hit.node_id, relative, "changed_source")
            )
            if relative in allowed_files:
                add_exact_slice(hit, relative, path, "changed_source")
            else:
                exact_blocked = True
            continue
        try:
            current_source_fingerprints(path, repo_root)
        except OSError:
            excluded.append(
                ExcludedContextHit(hit.node_id, relative, "unreadable_source")
            )
            continue
        requires_exact = (
            hit.node_type in request.require_exact_types
            or hit.node_type.lower() in {"document", "concept", "rationale"}
            or (
                sensitive_intent
                and hit.node_type
                in {"Evidence", "Status", "Artifact", "ReleaseEvidence"}
            )
        )
        if requires_exact and relative not in allowed_files:
            exact_blocked = True
            excluded.append(
                ExcludedContextHit(hit.node_id, relative, "outside_allowlist")
            )
            continue
        estimate = max(1, (len(hit.summary) + 3) // 4)
        if summary_tokens + estimate > summary_limit or len(accepted) >= top_k:
            excluded.append(
                ExcludedContextHit(hit.node_id, relative, "summary_budget_exceeded")
            )
            continue
        accepted.append(hit)
        summary_tokens += estimate
        if requires_exact:
            add_exact_slice(hit, relative, path, "current")
            for evidence in hit.evidence_path:
                evidence_resolved = _safe_relative(evidence, repo_root)
                if evidence_resolved is None:
                    continue
                evidence_relative, evidence_path = evidence_resolved
                if not evidence_path.is_file():
                    continue
                if evidence_relative not in allowed_files:
                    exact_blocked = True
                    continue
                if evidence_relative != relative:
                    add_full_file(evidence_relative, "unresolved_locator")

    if exact_blocked and not full_files:
        files, _ = _filesystem_files(request.filesystem_allowlist, repo_root)
        full_files.extend(files)
        full_file_reasons.append("exact_source_outside_allowlist")

    loaded_files = tuple(dict.fromkeys(full_files))
    full_file_tokens = 0
    for relative in loaded_files:
        path = repo_root / relative
        try:
            full_file_tokens += max(
                1, (len(path.read_text(encoding="utf-8")) + 3) // 4
            )
        except (OSError, UnicodeDecodeError):
            full_file_reasons.append("unreadable_full_file")

    estimated_tokens = summary_tokens + exact_tokens + full_file_tokens
    targeted_refresh = any(item.reason == "changed_source" for item in excluded)
    used_fallback = bool(loaded_files or exact_blocked or targeted_refresh)
    fallback_reason = None
    if exact_blocked:
        fallback_reason = "exact canonical source outside allowlist"
    elif loaded_files:
        fallback_reason = "full-file fallback required"
    elif targeted_refresh:
        fallback_reason = "changed source refreshed by exact slice"
    if estimated_tokens > total_limit and not loaded_files:
        used_fallback = True
        fallback_reason = "context exceeded stage total budget"
    budget = BudgetBreakdown(
        summary_tokens=summary_tokens,
        exact_tokens=exact_tokens,
        full_file_tokens=full_file_tokens,
        total_tokens=estimated_tokens,
        summary_limit=summary_limit,
        exact_limit=exact_limit,
        total_limit=total_limit,
        top_k=top_k,
    )
    return ContextResult(
        hits=tuple(accepted),
        loaded_files=loaded_files,
        used_fallback=used_fallback,
        fallback_reason=fallback_reason,
        estimated_tokens=estimated_tokens,
        summaries=tuple(accepted),
        exact_slices=tuple(exact_slices),
        excluded_hits=tuple(excluded),
        budget_breakdown=budget,
        full_file_fallback_reasons=tuple(dict.fromkeys(full_file_reasons)),
        exact_source_triggers=tuple(
            {
                (item.source_path, item.reason): item
                for item in source_triggers
            }.values()
        ),
        graph_health=health,
    )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Query project context through Graphify with fingerprint fallback."
    )
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--stage", required=True)
    parser.add_argument("--question", required=True)
    parser.add_argument("--route")
    parser.add_argument("--entity", action="append", default=[])
    parser.add_argument("--allow-file", action="append", default=[])
    parser.add_argument("--token-budget", type=int)
    parser.add_argument(
        "--migration-evidence",
        action="store_true",
        help="diagnostic opt-in for excluded migration archive evidence",
    )
    args = parser.parse_args()

    from graph_profile import load_graph_profile
    from graphify_provider import GraphifyJsonProvider

    repo_root = args.repo_root.resolve()
    profile_path = args.profile if args.profile.is_absolute() else repo_root / args.profile
    profile = load_graph_profile(profile_path, repo_root)
    configured_budget = profile.stage_budgets.get(args.stage)
    if configured_budget is None:
        parser.error("stage has no configured budget")
    query = GraphQuery(
        project_id=profile.project_id,
        stage=args.stage,
        question=args.question,
        route=args.route,
        entity_ids=tuple(args.entity),
        token_budget=args.token_budget or configured_budget,
        include_migration_evidence=args.migration_evidence,
    )
    request = ContextRequest(query, tuple(args.allow_file))
    result = route_context(
        request, GraphifyJsonProvider(profile, repo_root), repo_root
    )
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
