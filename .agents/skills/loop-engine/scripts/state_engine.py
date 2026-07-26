from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import NamedTemporaryFile


@dataclass(frozen=True)
class PageState:
    page_id: str
    route: str
    priority: str
    status: str
    stage: str
    blocker: str = ""
    iteration_stage: str = ""
    notes: str = ""


@dataclass(frozen=True)
class NextTask:
    page: str
    stage: str
    owner: str
    approval: str
    inputs: list[str] = field(default_factory=list)
    output: str = ""


@dataclass(frozen=True)
class LoopSignals:
    failed_build: bool = False
    failed_ci: bool = False
    pr_blocker: str = ""
    graph_state: str = "current"
    changed_fingerprint: bool = False
    disputed_claim: bool = False


@dataclass(frozen=True)
class SelectionResult:
    task: NextTask
    warnings: tuple[str, ...] = ()


class StateValidationError(ValueError):
    pass


TRANSITIONS = {
    "queued": {"contract_ready"},
    "contract_ready": {"creative_approved"},
    "creative_approved": {"copy_ready"},
    "copy_ready": {"assets_ready", "assets_not_needed"},
    "assets_ready": {"built"},
    "assets_not_needed": {"built"},
    "built": {"qa_passed"},
    "qa_passed": {"staging_ready"},
    "staging_ready": {"released"},
    "released": {"growth"},
    "growth": {"growth"},
}

STAGE_BY_STATUS = {
    "queued": "01-page-contract",
    "contract_ready": "02-creative-blueprint",
    "creative_approved": "03-conversion-copy",
    "copy_ready": "04-page-assets",
    "assets_ready": "05-full-page-build",
    "assets_not_needed": "05-full-page-build",
    "built": "06-integrated-qa-refinement",
    "qa_passed": "07-release-growth",
    "staging_ready": "07-release-growth",
    "released": "07-release-growth",
    "growth": "07-release-growth",
}

STAGE_OUTPUT = {
    "01-page-contract": "PAGE_CONTRACT.md",
    "02-creative-blueprint": "CREATIVE_BLUEPRINT.md",
    "03-conversion-copy": "PAGE_COPY.md",
    "04-page-assets": "ASSET_MANIFEST.md",
    "05-full-page-build": "BUILD_REPORT.md",
    "06-integrated-qa-refinement": "QA_REPORT.md",
    "07-release-growth": "RELEASE_GROWTH.md",
}

STAGE_INPUT_NAMES = {
    "01-page-contract": (),
    "02-creative-blueprint": ("PAGE_CONTRACT.md",),
    "03-conversion-copy": ("PAGE_CONTRACT.md", "CREATIVE_BLUEPRINT.md"),
    "04-page-assets": (
        "PAGE_CONTRACT.md",
        "CREATIVE_BLUEPRINT.md",
        "PAGE_COPY.md",
    ),
    "05-full-page-build": (
        "PAGE_CONTRACT.md",
        "CREATIVE_BLUEPRINT.md",
        "PAGE_COPY.md",
    ),
    "06-integrated-qa-refinement": (
        "PAGE_CONTRACT.md",
        "CREATIVE_BLUEPRINT.md",
        "PAGE_COPY.md",
        "BUILD_REPORT.md",
    ),
    "07-release-growth": ("QA_REPORT.md",),
}

STATUS_RU = {
    "queued": "В очереди",
    "contract_ready": "Контракт готов",
    "creative_approved": "Креативное направление согласовано",
    "copy_ready": "Текст готов",
    "assets_ready": "Ассеты готовы",
    "assets_not_needed": "Ассеты не нужны",
    "built": "Страница собрана",
    "qa_passed": "QA пройден",
    "staging_ready": "Готово к staging",
    "released": "Опубликовано",
    "growth": "Цикл роста",
}

STAGE_RU = {
    "01-page-contract": "Контракт страницы",
    "02-creative-blueprint": "Креативное направление",
    "03-conversion-copy": "Конверсионный текст",
    "04-page-assets": "Ассеты страницы",
    "05-full-page-build": "Полная сборка страницы",
    "06-integrated-qa-refinement": "Интегрированный QA и доработка",
    "07-release-growth": "Релиз и рост",
}

APPROVAL_RU = {
    "not_required": "не требуется",
    "creative_pending": "ожидается согласование креативного направления",
    "creative_approved": "креативное направление согласовано",
    "production_pending": "ожидается production-согласование",
    "production_approved": "production-согласование получено",
}


def validate_transition(old: str, new: str, approval: dict | None) -> list[str]:
    if new not in TRANSITIONS.get(old, set()):
        return [f"transition not allowed: {old} -> {new}"]
    if new == "creative_approved" and approval != {
        "scope": "creative",
        "state": "approved",
    }:
        return ["creative approval is required"]
    if new == "released" and approval != {
        "scope": "production",
        "state": "approved",
    }:
        return ["production approval is required"]
    return []


def _table_cells(line: str) -> list[str]:
    return [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]


def _is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(cell and set(cell) <= {"-", ":"} for cell in cells)


def parse_page_queue(text: str) -> list[PageState]:
    table_lines = [line for line in text.splitlines() if line.strip().startswith("|")]
    if len(table_lines) < 2:
        raise ValueError("PAGE_QUEUE table is missing")

    headers = _table_cells(table_lines[0])
    expected = [
        "Page ID",
        "Route",
        "Priority",
        "Status",
        "Stage",
        "Blocker",
        "Iteration Stage",
        "Notes",
    ]
    if headers != expected:
        raise ValueError(f"PAGE_QUEUE columns must be: {', '.join(expected)}")

    pages = []
    for line in table_lines[1:]:
        cells = _table_cells(line)
        if _is_separator_row(cells):
            continue
        if len(cells) != len(expected):
            raise ValueError(f"invalid PAGE_QUEUE row: {line}")
        page = PageState(
            page_id=cells[0],
            route=cells[1],
            priority=cells[2],
            status=cells[3],
            stage=cells[4],
            blocker=cells[5],
            iteration_stage=cells[6],
            notes=cells[7],
        )
        if page.status not in TRANSITIONS:
            raise ValueError(f"unknown page status: {page.status}")
        pages.append(page)
    return pages


def parse_next_task(text: str) -> NextTask:
    values = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        key, separator, raw = stripped[2:].partition(":")
        if separator:
            values[key.strip()] = raw.strip().strip("`")

    required = {"page", "stage", "owner", "approval", "inputs", "output"}
    missing = sorted(required - values.keys())
    if missing:
        raise ValueError("NEXT_TASK fields missing: " + ", ".join(missing))

    try:
        inputs = json.loads(values["inputs"])
    except json.JSONDecodeError as exc:
        raise ValueError("NEXT_TASK inputs must be an inline JSON list") from exc
    if not isinstance(inputs, list) or not all(isinstance(item, str) for item in inputs):
        raise ValueError("NEXT_TASK inputs must be a list of strings")

    return NextTask(
        page=values["page"],
        stage=values["stage"],
        owner=values["owner"],
        approval=values["approval"],
        inputs=inputs,
        output=values["output"],
    )


def _priority_key(page: PageState) -> tuple[int, str]:
    raw = page.priority.upper().removeprefix("P")
    return (int(raw) if raw.isdigit() else 999, page.page_id)


def _page_slug(page_id: str) -> str:
    slug = page_id.removeprefix("page-").strip()
    if not slug or "/" in slug or "\\" in slug or slug in {".", ".."}:
        raise StateValidationError(f"invalid page id: {page_id}")
    return slug


def _normal_task(
    page: PageState, configured_paths: dict[str, str] | None = None
) -> NextTask:
    stage = STAGE_BY_STATUS[page.status]
    slug = _page_slug(page.page_id)
    base = f"docs/pages/{slug}"
    inputs = [f"{base}/{name}" for name in STAGE_INPUT_NAMES[stage]]
    if stage == "01-page-contract":
        paths = configured_paths or {}
        inputs = [
            paths.get("page_queue", "docs/site/PAGE_QUEUE.md"),
            paths.get("master_context", "PROJECT_MASTER_CONTEXT.md"),
        ]

    approval = "not_required"
    if page.status == "contract_ready":
        approval = "creative_pending"
    elif page.status == "staging_ready":
        approval = "production_pending"

    return NextTask(
        page=page.page_id,
        stage=stage,
        owner=f"webpage-factory/{stage}",
        approval=approval,
        inputs=inputs,
        output=f"{base}/{STAGE_OUTPUT[stage]}",
    )


def select_next_task(
    pages: list[PageState],
    signals: LoopSignals | None = None,
    configured_paths: dict[str, str] | None = None,
) -> SelectionResult:
    if not pages:
        raise StateValidationError("PAGE_QUEUE has no pages")

    signals = signals or LoopSignals()
    page = sorted(pages, key=_priority_key)[0]
    warnings: list[str] = []

    if signals.failed_build or signals.failed_ci or signals.pr_blocker:
        reason = signals.pr_blocker or (
            "failed CI" if signals.failed_ci else "failed build"
        )
        return SelectionResult(
            NextTask(
                page=page.page_id,
                stage="repair",
                owner="loop-engine/loop-failed-build-repair",
                approval="not_required",
                inputs=[
                    "docs/system/NEXT_TASK.md",
                    "docs/release/PR_QUEUE.md",
                ],
                output="docs/system/FAILED_BUILD_REPAIR_REPORT.md",
            ),
            (f"repair preempts page work: {reason}",),
        )

    if signals.graph_state not in {"current", "stale", "unavailable"}:
        raise StateValidationError(f"unknown graph state: {signals.graph_state}")
    if signals.graph_state != "current":
        warnings.append(
            f"knowledge graph {signals.graph_state}; filesystem fallback required"
        )
    if signals.changed_fingerprint:
        warnings.append("source fingerprint changed; reload the exact canonical source")
    if signals.disputed_claim:
        warnings.append("disputed claim requires exact-file proof verification")

    task = _normal_task(page, configured_paths)
    if page.stage and page.stage != task.stage:
        warnings.append(
            f"stale recorded stage {page.stage}; lifecycle selects {task.stage}"
        )
    return SelectionResult(task, tuple(warnings))


def render_next_task(task: NextTask) -> str:
    return (
        "# NEXT_TASK\n\n"
        f"- page: {task.page}\n"
        f"- stage: {task.stage}\n"
        f"- owner: {task.owner}\n"
        f"- approval: {task.approval}\n"
        f"- inputs: {json.dumps(task.inputs, ensure_ascii=False)}\n"
        f"- output: {task.output}\n"
    )


def render_page_queue(pages: list[PageState]) -> str:
    lines = [
        "# PAGE_QUEUE",
        "",
        "| Page ID | Route | Priority | Status | Stage | Blocker | Iteration Stage | Notes |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for page in pages:
        values = (
            page.page_id,
            f"`{page.route}`",
            page.priority,
            page.status,
            page.stage,
            page.blocker,
            page.iteration_stage,
            page.notes,
        )
        if any("|" in value or "\n" in value for value in values):
            raise StateValidationError(f"unsafe PAGE_QUEUE value for {page.page_id}")
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def transition_page(
    pages: list[PageState],
    page_id: str,
    new_status: str,
    approval: dict | None = None,
    artifact_errors: list[str] | tuple[str, ...] = (),
) -> list[PageState]:
    if artifact_errors:
        raise StateValidationError(
            "artifact validation failed: " + "; ".join(artifact_errors)
        )

    updated: list[PageState] = []
    matched = False
    for page in pages:
        if page.page_id != page_id:
            updated.append(page)
            continue
        matched = True
        errors = validate_transition(page.status, new_status, approval)
        if errors:
            raise StateValidationError("; ".join(errors))
        stage = STAGE_BY_STATUS[new_status]
        updated.append(
            PageState(
                page_id=page.page_id,
                route=page.route,
                priority=page.priority,
                status=new_status,
                stage=stage,
                blocker="",
                iteration_stage=page.iteration_stage,
                notes=page.notes,
            )
        )
    if not matched:
        raise StateValidationError(f"page not found: {page_id}")
    return updated


def render_status_ru(pages: list[PageState], next_task: NextTask | None) -> str:
    lines = [
        "# STATUS",
        "",
        "## Панель владельца",
        "",
        "| Страница | Маршрут | Состояние | Текущий этап | Блокер |",
        "|---|---|---|---|---|",
    ]
    for page in pages:
        status = STATUS_RU.get(page.status, page.status)
        stage = STAGE_RU.get(page.stage, page.stage)
        lines.append(
            f"| {page.page_id} | `{page.route}` | {status} | "
            f"{stage} (`{page.stage}`) | {page.blocker or 'нет'} |"
        )

    lines.extend(["", "## Следующее действие", ""])
    if next_task is None:
        lines.append("- Безопасная задача не выбрана.")
    else:
        stage = STAGE_RU.get(next_task.stage, next_task.stage)
        approval = APPROVAL_RU.get(next_task.approval, next_task.approval)
        lines.extend(
            [
                f"- Страница: `{next_task.page}`",
                f"- Этап: {stage} (`{next_task.stage}`)",
                f"- Владелец: `{next_task.owner}`",
                f"- Требуется согласование: {approval} (`{next_task.approval}`)",
                f"- Результат: `{next_task.output}`",
            ]
        )

    return "\n".join(lines) + "\n"


def write_state_bundle(
    queue_path: Path,
    task_path: Path,
    status_path: Path,
    log_path: Path,
    pages: list[PageState],
    next_task: NextTask,
    log_entry: str,
) -> None:
    queue_content = render_page_queue(pages)
    task_content = render_next_task(next_task)
    status_content = render_status_ru(pages, next_task)
    existing_log = log_path.read_text(encoding="utf-8") if log_path.exists() else "# LOOP_LOG\n"
    log_content = existing_log.rstrip() + "\n\n" + log_entry.strip() + "\n"

    # Validate every derived document before the first target is replaced.
    parse_page_queue(queue_content)
    parse_next_task(task_content)
    targets = {
        queue_path: queue_content,
        task_path: task_content,
        status_path: status_content,
        log_path: log_content,
    }
    originals = {
        path: path.read_bytes() if path.exists() else None for path in targets
    }
    written: list[Path] = []
    try:
        for path, content in targets.items():
            atomic_write(path, content)
            written.append(path)
    except OSError:
        for path in reversed(written):
            original = originals[path]
            if original is None:
                path.unlink(missing_ok=True)
            else:
                atomic_write(path, original.decode("utf-8"))
        raise


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="\n",
        dir=path.parent,
        delete=False,
    ) as temporary:
        temporary.write(content)
        temporary_path = Path(temporary.name)
    temporary_path.replace(path)
