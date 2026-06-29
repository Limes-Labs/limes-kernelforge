#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.agent_notes_guard import load_json, validate_notes


ROOT = Path(__file__).resolve().parents[1]


def resolve(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Limes KernelForge agent notes.")
    parser.add_argument("--input", required=True, help="Agent notes JSON.")
    args = parser.parse_args()

    notes_path = resolve(args.input)
    notes = load_json(notes_path)
    errors = validate_notes(notes)
    report = {
        "ok": not errors,
        "challenge": notes.get("challenge"),
        "input": str(notes_path),
        "errors": errors,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
