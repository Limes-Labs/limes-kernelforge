#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.search_ledger_guard import load_json, validate_ledger


ROOT = Path(__file__).resolve().parents[1]


def resolve(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Limes KernelForge search ledger.")
    parser.add_argument("--input", required=True, help="Search ledger JSON.")
    args = parser.parse_args()

    ledger_path = resolve(args.input)
    ledger = load_json(ledger_path)
    errors = validate_ledger(ledger)
    report = {
        "ok": not errors,
        "challenge": ledger.get("challenge"),
        "input": str(ledger_path),
        "attempts": len(ledger.get("attempts", [])) if isinstance(ledger.get("attempts"), list) else None,
        "errors": errors,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
