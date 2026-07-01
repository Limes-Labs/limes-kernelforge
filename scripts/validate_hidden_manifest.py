#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.hidden_manifest_guard import load_json, validate_hidden_manifest


ROOT = Path(__file__).resolve().parents[1]


def resolve(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a KernelForge trusted hidden-case manifest.")
    parser.add_argument("--input", required=True, help="Hidden manifest JSON.")
    parser.add_argument("--contract", default="verifier/replay-contract.json")
    args = parser.parse_args()

    manifest_path = resolve(args.input)
    contract_path = resolve(args.contract)
    manifest = load_json(manifest_path)
    contract = load_json(contract_path)
    errors = validate_hidden_manifest(manifest, contract)
    report = {
        "ok": not errors,
        "challenge": manifest.get("challenge"),
        "input": str(manifest_path),
        "hidden_manifest_ready": manifest.get("hidden_manifest_ready"),
        "case_suite_count": len(manifest.get("case_suites", []))
        if isinstance(manifest.get("case_suites"), list)
        else None,
        "runner_track_count": len(manifest.get("runner_tracks", []))
        if isinstance(manifest.get("runner_tracks"), list)
        else None,
        "errors": errors,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
