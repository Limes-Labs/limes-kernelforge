#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.source_bundle_guard import build_source_bundle, dumps_report
from harness.submission_guard import load_json


ROOT = Path(__file__).resolve().parents[1]


def git_changed_paths(base: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def git_head_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def resolve_path(raw_path: str) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = ROOT / path
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a hashed KernelForge editable-source bundle.")
    parser.add_argument("--challenge", default="challenge.json", help="Challenge contract JSON.")
    parser.add_argument("--base", default="origin/main", help="Base ref for git diff mode.")
    parser.add_argument("--commit", help="Source commit SHA. Defaults to git rev-parse HEAD.")
    parser.add_argument("--output", help="Optional JSON output path.")
    parser.add_argument(
        "--changed-file",
        action="append",
        default=[],
        help="Explicit changed file. Repeat to avoid git diff mode.",
    )
    args = parser.parse_args()

    contract = load_json(resolve_path(args.challenge))
    changed_paths = args.changed_file or git_changed_paths(args.base)
    report = build_source_bundle(
        contract=contract,
        changed_paths=changed_paths,
        source_commit=args.commit or git_head_commit(),
        root=ROOT,
    )
    if args.output:
        resolve_path(args.output).write_text(
            json.dumps(report["bundle"], indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(dumps_report(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
