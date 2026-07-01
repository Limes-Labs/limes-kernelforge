#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.public_baseline_guard import (
    DEFAULT_BASELINE,
    current_public_baseline,
    dumps_report,
    load_json,
    validate_public_baseline,
)


ROOT = Path(__file__).resolve().parents[1]


def resolve(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the KernelForge public smoke baseline contract.")
    parser.add_argument("--input", default=str(DEFAULT_BASELINE.relative_to(ROOT)), help="Locked public baseline JSON.")
    parser.add_argument(
        "--print-current",
        action="store_true",
        help="Print the current public baseline JSON instead of validating an input file.",
    )
    args = parser.parse_args()

    if args.print_current:
        print(json.dumps(current_public_baseline(), indent=2, sort_keys=True))
        return 0

    baseline_path = resolve(args.input)
    expected = load_json(baseline_path)
    report = validate_public_baseline(expected=expected)
    report["baseline"] = str(baseline_path)
    print(dumps_report(report), end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
