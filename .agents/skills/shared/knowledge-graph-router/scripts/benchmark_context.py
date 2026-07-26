from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path, PurePosixPath


def compare_context(filesystem_tokens: int, graph_tokens: int) -> dict[str, float | int]:
    saved = max(0, filesystem_tokens - graph_tokens)
    reduction = (saved / filesystem_tokens * 100) if filesystem_tokens else 0.0
    return {
        "filesystem_tokens": filesystem_tokens,
        "graph_tokens": graph_tokens,
        "saved_tokens": saved,
        "reduction_percent": round(reduction, 2),
    }


def _safe_file(repo_root: Path, value: str) -> tuple[str, Path]:
    pure = PurePosixPath(value.replace("\\", "/"))
    if pure.is_absolute() or any(part == ".." for part in pure.parts):
        raise ValueError(f"benchmark path escapes repository: {value}")
    path = (repo_root / Path(*pure.parts)).resolve()
    path.relative_to(repo_root.resolve())
    if not path.is_file():
        raise ValueError(f"benchmark file is missing: {value}")
    return pure.as_posix(), path


def _tokens(path: Path) -> int:
    return max(1, (len(path.read_text(encoding="utf-8")) + 3) // 4)


def _load_cases(path: Path, project_id: str) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != "1.0":
        raise ValueError("invalid benchmark cases schema")
    if data.get("project_id") != project_id:
        raise ValueError("benchmark cases project_id does not match profile")
    cases = data.get("cases")
    if not isinstance(cases, dict):
        raise ValueError("benchmark cases must be an object")
    return cases


def run_benchmark(
    profile_path: Path,
    repo_root: Path,
    stages: tuple[str, ...],
) -> tuple[dict, str]:
    from graph_profile import load_graph_profile
    from graphify_provider import GraphifyJsonProvider
    from provider import ContextRequest, GraphQuery
    from query_context import route_context

    profile = load_graph_profile(profile_path, repo_root)
    if not profile.benchmark_cases_path:
        raise ValueError("profile has no benchmark_cases_path")
    cases_path = repo_root / profile.benchmark_cases_path
    cases = _load_cases(cases_path, profile.project_id)
    provider = GraphifyJsonProvider(profile, repo_root)
    health = provider.health(profile)
    results = []
    total_filesystem = 0
    total_graph = 0

    for stage in stages:
        case = cases.get(stage)
        if not isinstance(case, dict):
            raise ValueError(f"benchmark case is missing: {stage}")
        allowlist = case.get("filesystem_allowlist")
        exact = case.get("required_exact_files", [])
        question = case.get("question")
        route = case.get("route")
        if (
            not isinstance(allowlist, list)
            or not isinstance(exact, list)
            or not isinstance(question, str)
            or not question.strip()
        ):
            raise ValueError(f"invalid benchmark case: {stage}")
        resolved_allowlist = [_safe_file(repo_root, str(value)) for value in allowlist]
        resolved_exact = [_safe_file(repo_root, str(value)) for value in exact]
        filesystem_tokens = sum(_tokens(path) for _, path in resolved_allowlist)
        query = GraphQuery(
            project_id=profile.project_id,
            stage=stage,
            question=question,
            route=route if isinstance(route, str) else None,
            token_budget=profile.stage_budgets[stage],
        )
        routed = route_context(
            ContextRequest(query, tuple(relative for relative, _ in resolved_allowlist)),
            provider,
            repo_root,
        )
        routed_loaded = set(routed.loaded_files)
        exact_tokens = sum(
            _tokens(path)
            for relative, path in resolved_exact
            if relative not in routed_loaded
        )
        graph_tokens = routed.estimated_tokens + exact_tokens
        cited_sources = sorted(
            set(routed.loaded_files)
            | {hit.source_path for hit in routed.hits}
            | {relative for relative, _ in resolved_exact}
        )
        exact_coverage = all(relative in cited_sources for relative, _ in resolved_exact)
        comparison = compare_context(filesystem_tokens, graph_tokens)
        passed = bool(
            health.available
            and health.fresh
            and routed.hits
            and exact_coverage
            and graph_tokens < filesystem_tokens
        )
        results.append(
            {
                "stage": stage,
                **comparison,
                "hit_count": len(routed.hits),
                "cited_source_count": len(cited_sources),
                "required_exact_coverage": exact_coverage,
                "fallback": routed.used_fallback,
                "fallback_reason": routed.fallback_reason,
                "answer_equivalence_proxy": "PASS" if passed else "FAIL",
                "cited_sources": cited_sources,
            }
        )
        total_filesystem += filesystem_tokens
        total_graph += graph_tokens

    total = compare_context(total_filesystem, total_graph)
    payload = {
        "project_id": profile.project_id,
        "graph_health": asdict(health),
        "cases": results,
        "total": total,
        "pass": all(item["answer_equivalence_proxy"] == "PASS" for item in results),
    }
    lines = [
        "# CONTEXT_BENCHMARK",
        "",
        f"- project_id: `{profile.project_id}`",
        f"- graph_available: `{str(health.available).lower()}`",
        f"- graph_fresh: `{str(health.fresh).lower()}`",
        f"- graph_nodes: `{health.node_count}`",
        f"- graph_edges: `{health.edge_count}`",
        f"- overall: `{'PASS' if payload['pass'] else 'FAIL'}`",
        "",
        "| Stage | Filesystem tokens | Graph-first tokens | Reduction | Hits | Exact coverage | Fallback | Verdict |",
        "|---|---:|---:|---:|---:|---|---|---|",
    ]
    for item in results:
        lines.append(
            f"| {item['stage']} | {item['filesystem_tokens']} | {item['graph_tokens']} | "
            f"{item['reduction_percent']}% | {item['hit_count']} | "
            f"{'PASS' if item['required_exact_coverage'] else 'FAIL'} | "
            f"{'yes' if item['fallback'] else 'no'} | {item['answer_equivalence_proxy']} |"
        )
    lines.extend(
        [
            "",
            f"Итого: {total['filesystem_tokens']} → {total['graph_tokens']} токенов; "
            f"сокращение {total['reduction_percent']}%.",
            "",
            "Методика: filesystem baseline загружает полный allowlist стадии; graph-first учитывает "
            "компактные проверяемые summaries и обязательное точное чтение safety-critical файлов. "
            "Answer-equivalence proxy требует свежий граф, непустые hits, полное покрытие exact sources "
            "и меньшее потребление контекста.",
            "",
            "```json",
            json.dumps(payload, ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    )
    return payload, "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare filesystem-only and graph-first context token estimates."
    )
    parser.add_argument("--filesystem-tokens", type=int)
    parser.add_argument("--graph-tokens", type=int)
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--stages", nargs="+")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.profile is None:
        if args.filesystem_tokens is None or args.graph_tokens is None:
            parser.error("provide token estimates or --profile with --stages and --output")
        if args.filesystem_tokens < 0 or args.graph_tokens < 0:
            parser.error("token estimates must be non-negative")
        print(json.dumps(compare_context(args.filesystem_tokens, args.graph_tokens)))
        return 0

    if not args.stages or args.output is None:
        parser.error("--profile requires --stages and --output")
    repo_root = args.repo_root.resolve()
    profile_path = args.profile if args.profile.is_absolute() else repo_root / args.profile
    output = args.output if args.output.is_absolute() else repo_root / args.output
    output.resolve().relative_to(repo_root)
    payload, report = run_benchmark(profile_path, repo_root, tuple(args.stages))
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(report, encoding="utf-8")
    temporary.replace(output)
    print(json.dumps(payload["total"], ensure_ascii=False))
    print(f"PASS: wrote {output.relative_to(repo_root).as_posix()}" if payload["pass"] else "FAIL: benchmark gates")
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
