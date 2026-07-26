from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path, PurePosixPath
import re
import sys

from fingerprints import current_source_fingerprints
from provider import (
    ContextRequest,
    ContextResult,
    GraphContextHit,
    GraphQuery,
    KnowledgeGraphProvider,
)

SENSITIVE_INTENT = re.compile(
    r"(?:claim|proof|approval|conflict|release|production|утвержден|доказ|согласован|конфликт|спор|релиз)",
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


def _fallback(request: ContextRequest, repo_root: Path, reason: str) -> ContextResult:
    files, tokens = _filesystem_files(request.filesystem_allowlist, repo_root)
    return ContextResult((), files, True, reason, tokens)


def route_context(
    request: ContextRequest,
    provider: KnowledgeGraphProvider,
    repo_root: Path,
) -> ContextResult:
    profile = getattr(provider, "profile", None)
    stage_budgets = getattr(profile, "stage_budgets", {})
    stage_budget = stage_budgets.get(request.query.stage)
    if not isinstance(stage_budget, int) or stage_budget <= 0:
        return _fallback(request, repo_root, "stage budget unavailable")
    effective_budget = min(request.query.token_budget, stage_budget)
    effective_query = replace(request.query, token_budget=effective_budget)
    try:
        health = provider.health(profile)
    except Exception as exc:  # provider boundary must preserve filesystem operation
        return _fallback(request, repo_root, f"graph unavailable: {exc}")
    if not health.available:
        return _fallback(request, repo_root, "graph unavailable")
    if not health.fresh:
        return _fallback(request, repo_root, "graph stale")

    try:
        candidate_hits = provider.query(effective_query)
    except Exception as exc:
        return _fallback(request, repo_root, f"graph query unavailable: {exc}")
    if any(hit.project_id != effective_query.project_id for hit in candidate_hits):
        return _fallback(request, repo_root, "cross-project graph result rejected")

    allowed_files = set(request.filesystem_allowlist)
    accepted: list[GraphContextHit] = []
    exact_files: list[str] = []
    stale_found = False
    exact_blocked = False
    sensitive_intent = bool(SENSITIVE_INTENT.search(effective_query.question))
    estimated_tokens = 0
    for hit in candidate_hits:
        resolved = _safe_relative(hit.source_path, repo_root)
        if resolved is None:
            stale_found = True
            continue
        relative, path = resolved
        if not path.is_file() or not hit.source_fingerprint:
            stale_found = True
            continue
        try:
            current = current_source_fingerprints(path, repo_root)
        except OSError:
            stale_found = True
            continue
        if hit.source_fingerprint not in current:
            stale_found = True
            if relative in allowed_files:
                exact_files.append(relative)
            continue
        requires_exact = (
            hit.node_type in request.require_exact_types
            or hit.node_type.lower() in {"document", "concept", "rationale"}
            or sensitive_intent
        )
        if requires_exact and relative not in allowed_files:
            exact_blocked = True
            continue
        estimate = max(1, (len(hit.summary) + 3) // 4)
        if estimated_tokens + estimate > effective_budget:
            continue
        accepted.append(hit)
        estimated_tokens += estimate
        if requires_exact:
            exact_files.append(relative)
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
                exact_files.append(evidence_relative)

    loaded_files = tuple(dict.fromkeys(exact_files))
    for relative in loaded_files:
        path = repo_root / relative
        try:
            estimated_tokens += max(1, (len(path.read_text(encoding="utf-8")) + 3) // 4)
        except (OSError, UnicodeDecodeError):
            stale_found = True

    if stale_found or exact_blocked:
        if not loaded_files:
            files, file_tokens = _filesystem_files(request.filesystem_allowlist, repo_root)
            loaded_files = files
            estimated_tokens += file_tokens
        reason = (
            "exact canonical source outside allowlist"
            if exact_blocked
            else "stale graph fingerprint"
        )
        return ContextResult(tuple(accepted), loaded_files, True, reason, estimated_tokens)
    if estimated_tokens > effective_budget:
        return ContextResult(
            tuple(accepted),
            loaded_files,
            True,
            "exact-file safety exceeded soft stage budget",
            estimated_tokens,
        )
    return ContextResult(tuple(accepted), loaded_files, False, None, estimated_tokens)


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
    )
    request = ContextRequest(query, tuple(args.allow_file))
    result = route_context(
        request, GraphifyJsonProvider(profile, repo_root), repo_root
    )
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
