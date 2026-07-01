#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.source_bundle_guard import dumps_report, validate_source_bundle
from harness.submission_guard import load_json


ROOT = Path(__file__).resolve().parents[1]


def resolve_path(raw_path: str) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = ROOT / path
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a KernelForge editable-source bundle.")
    parser.add_argument("--input", required=True, help="Source bundle JSON.")
    parser.add_argument("--challenge", default="challenge.json", help="Challenge contract JSON.")
    parser.add_argument("--commit", help="Expected source commit SHA.")
    parser.add_argument(
        "--changed-file",
        action="append",
        default=[],
        help="Explicit changed file. Repeat to compare against a checked diff.",
    )
    args = parser.parse_args()

    bundle = load_json(resolve_path(args.input))
    contract = load_json(resolve_path(args.challenge))
    report = validate_source_bundle(
        bundle=bundle,
        contract=contract,
        root=ROOT,
        changed_paths=args.changed_file or None,
        source_commit=args.commit,
    )
    report["input"] = str(resolve_path(args.input))
    print(dumps_report(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
