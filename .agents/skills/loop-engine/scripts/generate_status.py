from __future__ import annotations

import argparse
from pathlib import Path

from state_engine import (
    atomic_write,
    parse_next_task,
    parse_page_queue,
    render_status_ru,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate the Russian project owner STATUS dashboard."
    )
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    pages = parse_page_queue(args.queue.read_text(encoding="utf-8"))
    task = parse_next_task(args.task.read_text(encoding="utf-8"))
    atomic_write(args.output, render_status_ru(pages, task))
    print(f"PASS: generated Russian STATUS at {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
