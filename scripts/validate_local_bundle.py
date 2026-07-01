#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.local_bundle_guard import validate_local_bundle
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


def resolve_path(raw_path: str) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = ROOT / path
    return path


def manifest_search_ledger_path(manifest: dict[str, Any], explicit_path: str | None) -> Path | None:
    raw_path = explicit_path
    if raw_path is None:
        search_ledger = manifest.get("search_ledger", {})
        if isinstance(search_ledger, dict):
            value = search_ledger.get("path")
            raw_path = value if isinstance(value, str) else None
    if raw_path is None or not raw_path.strip() or raw_path.strip().startswith("<"):
        return None
    return resolve_path(raw_path)


def manifest_source_bundle_path(manifest: dict[str, Any], explicit_path: str | None) -> Path | None:
    raw_path = explicit_path
    if raw_path is None:
        source_bundle = manifest.get("source_bundle", {})
        if isinstance(source_bundle, dict):
            value = source_bundle.get("path")
            raw_path = value if isinstance(value, str) else None
    if raw_path is None or not raw_path.strip() or raw_path.strip().startswith("<"):
        return None
    return resolve_path(raw_path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate that a KernelForge submission bundle matches a fresh local correctness run."
    )
    parser.add_argument("--manifest", required=True, help="Completed submission manifest JSON.")
    parser.add_argument("--challenge", default="challenge.json", help="Challenge contract JSON.")
    parser.add_argument("--search-ledger", help="Completed search ledger JSON. Defaults to manifest search_ledger.path.")
    parser.add_argument("--source-bundle", help="Completed source bundle JSON. Defaults to manifest source_bundle.path.")
    parser.add_argument("--base", default="origin/main", help="Base ref for git diff mode.")
    parser.add_argument(
        "--changed-file",
        action="append",
        default=[],
        help="Explicit changed file. Repeat to avoid git diff mode.",
    )
    args = parser.parse_args()

    manifest_path = resolve_path(args.manifest)
    challenge_path = resolve_path(args.challenge)

    manifest = load_json(manifest_path)
    contract = load_json(challenge_path)
    changed_paths = args.changed_file or git_changed_paths(args.base)

    search_ledger_path = manifest_search_ledger_path(manifest, args.search_ledger)
    source_bundle_path = manifest_source_bundle_path(manifest, args.source_bundle)
    search_ledger = None
    source_bundle = None
    load_errors: list[str] = []
    if search_ledger_path is None:
        load_errors.append("search ledger path was not provided and manifest search_ledger.path is not concrete")
    elif not search_ledger_path.exists():
        load_errors.append(f"search ledger path does not exist: {search_ledger_path}")
    else:
        search_ledger = load_json(search_ledger_path)
    if source_bundle_path is None:
        load_errors.append("source bundle path was not provided and manifest source_bundle.path is not concrete")
    elif not source_bundle_path.exists():
        load_errors.append(f"source bundle path does not exist: {source_bundle_path}")
    else:
        source_bundle = load_json(source_bundle_path)

    report = validate_local_bundle(
        manifest=manifest,
        contract=contract,
        changed_paths=changed_paths,
        search_ledger=search_ledger,
        source_bundle=source_bundle,
    )
    report["manifest"] = str(manifest_path)
    report["search_ledger"] = str(search_ledger_path) if search_ledger_path else None
    report["source_bundle"] = str(source_bundle_path) if source_bundle_path else None
    if load_errors:
        report["errors"].extend(load_errors)
        report["ok"] = False
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
