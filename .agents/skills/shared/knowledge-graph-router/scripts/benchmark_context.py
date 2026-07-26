from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path, PurePosixPath
import re


FACTORY_STAGES = (
    "01-page-contract",
    "02-creative-blueprint",
    "03-conversion-copy",
    "04-page-assets",
    "05-full-page-build",
    "06-integrated-qa-refinement",
    "07-release-growth",
)
DISALLOWED_EXCLUSIONS = {
    "changed_source",
    "changed_dependency",
    "migration_evidence",
    "cross_project",
    "cross_route",
    "stage_mismatch",
    "excluded",
}


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


def _validate_case(case: object, case_id: str) -> dict:
    if not isinstance(case, dict):
        raise ValueError(f"invalid benchmark case: {case_id}")
    required = (
        "route",
        "stage",
        "question",
        "filesystem_allowlist",
        "required_facts",
        "required_exact_locators",
    )
    if any(key not in case for key in required):
        raise ValueError(f"invalid benchmark case: {case_id}")
    if case["stage"] not in FACTORY_STAGES:
        raise ValueError(f"invalid benchmark stage: {case_id}")
    if not isinstance(case["route"], str) or not case["route"]:
        raise ValueError(f"invalid benchmark route: {case_id}")
    if not isinstance(case["question"], str) or not case["question"].strip():
        raise ValueError(f"invalid benchmark question: {case_id}")
    for key in ("filesystem_allowlist", "required_facts", "required_exact_locators"):
        if not isinstance(case[key], list) or any(
            not isinstance(item, str) or not item.strip() for item in case[key]
        ):
            raise ValueError(f"invalid benchmark {key}: {case_id}")
    normalized = dict(case)
    normalized.setdefault("id", case_id)
    return normalized


def _load_cases(path: Path, project_id: str) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") not in {"1.0", "1.1"}:
        raise ValueError("invalid benchmark cases schema")
    if data.get("project_id") != project_id:
        raise ValueError("benchmark cases project_id does not match profile")
    cases = data.get("cases")
    if data["schema_version"] == "1.0":
        if not isinstance(cases, dict):
            raise ValueError("benchmark cases must be an object")
        migrated = []
        for stage, raw in cases.items():
            if not isinstance(raw, dict):
                raise ValueError(f"invalid benchmark case: {stage}")
            case = dict(raw)
            case["stage"] = stage
            case["id"] = f"{case.get('route', '/') or '/'}:{stage}"
            case["required_facts"] = list(case.get("required_facts", []))
            case["required_exact_locators"] = list(
                case.get("required_exact_locators", [])
            )
            migrated.append(_validate_case(case, case["id"]))
        return migrated
    if not isinstance(cases, list):
        raise ValueError("schema 1.1 benchmark cases must be a list")
    normalized = [
        _validate_case(case, str(case.get("id", index)) if isinstance(case, dict) else str(index))
        for index, case in enumerate(cases)
    ]
    identities = [(case["route"], case["stage"]) for case in normalized]
    if len(identities) != len(set(identities)):
        raise ValueError("benchmark route/stage cases must be unique")
    return normalized


def _normalized_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).casefold()


def evaluate_case_gates(
    *,
    required_facts: list[str],
    required_exact_locators: list[str],
    evidence_text: str,
    exact_locators: set[str],
    loaded_files: tuple[str, ...],
    excluded_reasons: tuple[str, ...],
    total_tokens: int,
    total_limit: int,
) -> dict[str, object]:
    normalized_evidence = _normalized_text(evidence_text)
    found_facts = [
        fact for fact in required_facts if _normalized_text(fact) in normalized_evidence
    ]
    found_locators = [
        locator for locator in required_exact_locators if locator in exact_locators
    ]
    fact_percent = (
        len(found_facts) / len(required_facts) * 100 if required_facts else 100.0
    )
    exact_percent = (
        len(found_locators) / len(required_exact_locators) * 100
        if required_exact_locators
        else 100.0
    )
    disallowed = sorted(set(excluded_reasons).intersection(DISALLOWED_EXCLUSIONS))
    passed = bool(
        fact_percent == 100.0
        and exact_percent == 100.0
        and not loaded_files
        and not disallowed
        and total_tokens <= total_limit
    )
    return {
        "passed": passed,
        "required_fact_coverage_percent": round(fact_percent, 2),
        "exact_slice_coverage_percent": round(exact_percent, 2),
        "missing_facts": [fact for fact in required_facts if fact not in found_facts],
        "missing_exact_locators": [
            locator for locator in required_exact_locators if locator not in found_locators
        ],
        "disallowed_exclusions": disallowed,
        "full_file_count": len(loaded_files),
        "within_total_budget": total_tokens <= total_limit,
    }


def run_benchmark(
    profile_path: Path,
    repo_root: Path,
    stages: tuple[str, ...] | None = None,
) -> tuple[dict, str]:
    from graph_profile import load_graph_profile
    from graphify_provider import GraphifyJsonProvider
    from provider import ContextRequest, GraphQuery
    from query_context import route_context

    profile = load_graph_profile(profile_path, repo_root)
    if not profile.benchmark_cases_path:
        raise ValueError("profile has no benchmark_cases_path")
    cases = _load_cases(repo_root / profile.benchmark_cases_path, profile.project_id)
    selected = set(stages or FACTORY_STAGES)
    cases = [case for case in cases if case["stage"] in selected]
    if not cases:
        raise ValueError("no benchmark cases selected")
    provider = GraphifyJsonProvider(profile, repo_root)
    health = provider.health(profile)
    results = []
    total_filesystem = 0
    total_graph = 0

    for case in cases:
        allowlist = [_safe_file(repo_root, value) for value in case["filesystem_allowlist"]]
        filesystem_tokens = sum(_tokens(path) for _, path in allowlist)
        stage = case["stage"]
        query = GraphQuery(
            project_id=profile.project_id,
            stage=stage,
            question=case["question"],
            route=case["route"],
            token_budget=profile.stage_budgets[stage],
        )
        routed = route_context(
            ContextRequest(query, tuple(relative for relative, _ in allowlist)),
            provider,
            repo_root,
        )
        evidence_text = "\n".join(
            [hit.summary for hit in routed.hits]
            + [item.text for item in routed.exact_slices]
        )
        gates = evaluate_case_gates(
            required_facts=case["required_facts"],
            required_exact_locators=case["required_exact_locators"],
            evidence_text=evidence_text,
            exact_locators={item.source_locator for item in routed.exact_slices},
            loaded_files=routed.loaded_files,
            excluded_reasons=tuple(item.reason for item in routed.excluded_hits),
            total_tokens=routed.estimated_tokens,
            total_limit=routed.budget_breakdown.total_limit,
        )
        comparison = compare_context(filesystem_tokens, routed.estimated_tokens)
        passed = bool(
            health.available
            and getattr(health, "state", "unavailable") != "unavailable"
            and (routed.hits or routed.exact_slices)
            and gates["passed"]
            and comparison["reduction_percent"] >= 60.0
        )
        results.append(
            {
                "id": case["id"],
                "route": case["route"],
                "stage": stage,
                **comparison,
                "hit_count": len(routed.hits),
                "exact_slice_count": len(routed.exact_slices),
                "fallback": routed.used_fallback,
                "fallback_reason": routed.fallback_reason,
                **gates,
                "answer_equivalence_proxy": "PASS" if passed else "FAIL",
                "hit_ids": [hit.node_id for hit in routed.hits],
                "exact_locators": [item.source_locator for item in routed.exact_slices],
                "excluded_reasons": [item.reason for item in routed.excluded_hits],
            }
        )
        total_filesystem += filesystem_tokens
        total_graph += routed.estimated_tokens

    total = compare_context(total_filesystem, total_graph)
    matrix = {(item["route"], item["stage"]) for item in results}
    routes = {case["route"] for case in cases}
    expected_matrix = {(route, stage) for route in routes for stage in selected}
    matrix_complete = len(routes) >= 2 and matrix == expected_matrix
    payload = {
        "project_id": profile.project_id,
        "graph_health": asdict(health),
        "cases": results,
        "matrix_complete": matrix_complete,
        "total": total,
        "pass": bool(
            matrix_complete
            and total["reduction_percent"] >= 60.0
            and all(item["answer_equivalence_proxy"] == "PASS" for item in results)
        ),
    }
    lines = [
        "# CONTEXT_BENCHMARK",
        "",
        f"- project_id: `{profile.project_id}`",
        f"- graph_state: `{health.state}`",
        f"- graph_nodes: `{health.node_count}`",
        f"- graph_edges: `{health.edge_count}`",
        f"- matrix_complete: `{str(payload['matrix_complete']).lower()}`",
        f"- overall: `{'PASS' if payload['pass'] else 'FAIL'}`",
        "",
        "| Route | Stage | Filesystem | Graph | Reduction | Facts | Exact | Full files | Budget | Verdict |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for item in results:
        lines.append(
            f"| {item['route']} | {item['stage']} | {item['filesystem_tokens']} | "
            f"{item['graph_tokens']} | {item['reduction_percent']}% | "
            f"{item['required_fact_coverage_percent']}% | {item['exact_slice_coverage_percent']}% | "
            f"{item['full_file_count']} | {'PASS' if item['within_total_budget'] else 'FAIL'} | "
            f"{item['answer_equivalence_proxy']} |"
        )
    lines.extend(
        [
            "",
            f"РС‚РѕРіРѕ: {total['filesystem_tokens']} в†’ {total['graph_tokens']} С‚РѕРєРµРЅРѕРІ; "
            f"СЃРѕРєСЂР°С‰РµРЅРёРµ {total['reduction_percent']}%.",
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
            parser.error("provide token estimates or --profile with --output")
        if args.filesystem_tokens < 0 or args.graph_tokens < 0:
            parser.error("token estimates must be non-negative")
        print(json.dumps(compare_context(args.filesystem_tokens, args.graph_tokens)))
        return 0

    if args.output is None:
        parser.error("--profile requires --output")
    repo_root = args.repo_root.resolve()
    profile_path = args.profile if args.profile.is_absolute() else repo_root / args.profile
    output = args.output if args.output.is_absolute() else repo_root / args.output
    output.resolve().relative_to(repo_root)
    payload, report = run_benchmark(
        profile_path,
        repo_root,
        tuple(args.stages) if args.stages else None,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(report, encoding="utf-8")
    temporary.replace(output)
    print(json.dumps(payload["total"], ensure_ascii=False))
    print(
        f"PASS: wrote {output.relative_to(repo_root).as_posix()}"
        if payload["pass"]
        else "FAIL: benchmark gates"
    )
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
