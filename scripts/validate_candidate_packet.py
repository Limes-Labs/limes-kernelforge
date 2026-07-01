#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.candidate_packet_guard import validate_packet
from harness.submission_guard import load_json


ROOT = Path(__file__).resolve().parents[1]


def resolve(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a KernelForge local candidate packet.")
    parser.add_argument("--input", required=True, help="Candidate packet JSON.")
    parser.add_argument("--challenge", default="challenge.json")
    parser.add_argument("--schema-only", action="store_true", help="Validate schema without reading artifact files.")
    args = parser.parse_args()

    packet_path = resolve(args.input)
    packet = load_json(packet_path)
    contract = load_json(resolve(args.challenge))
    errors = validate_packet(packet, contract, root=ROOT, verify_files=not args.schema_only)
    report = {
        "ok": not errors,
        "challenge": packet.get("challenge"),
        "input": str(packet_path),
        "packet_id": packet.get("packet_id"),
        "candidate_ready": packet.get("candidate_ready"),
        "errors": errors,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
