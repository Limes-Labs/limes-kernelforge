#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.submission_guard import load_json, validate_submission


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Limes KernelForge submission manifest.")
    parser.add_argument("--manifest", required=True, help="Completed submission manifest JSON.")
    parser.add_argument("--challenge", default="challenge.json", help="Challenge contract JSON.")
    parser.add_argument("--base", default="origin/main", help="Base ref for git diff mode.")
    parser.add_argument(
        "--changed-file",
        action="append",
        default=[],
        help="Explicit changed file. Repeat to avoid git diff mode.",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    challenge_path = Path(args.challenge)
    if not manifest_path.is_absolute():
        manifest_path = ROOT / manifest_path
    if not challenge_path.is_absolute():
        challenge_path = ROOT / challenge_path

    changed_paths = args.changed_file or git_changed_paths(args.base)
    manifest = load_json(manifest_path)
    contract = load_json(challenge_path)
    errors = validate_submission(manifest, contract, changed_paths)
    report = {
        "ok": not errors,
        "challenge": contract.get("id"),
        "manifest": str(manifest_path),
        "changed_files": changed_paths,
        "errors": errors,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
