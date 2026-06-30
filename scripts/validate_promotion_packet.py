#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.promotion_packet_guard import load_json, validate_packet


ROOT = Path(__file__).resolve().parents[1]


def resolve(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Limes KernelForge promotion packet.")
    parser.add_argument("--input", required=True, help="Promotion packet JSON.")
    parser.add_argument(
        "--contract",
        default="verifier/replay-contract.json",
        help="Verifier replay contract JSON. Defaults to verifier/replay-contract.json.",
    )
    args = parser.parse_args()

    packet_path = resolve(args.input)
    contract_path = resolve(args.contract)
    packet = load_json(packet_path)
    contract = load_json(contract_path)
    errors = validate_packet(packet, contract)
    report = {
        "ok": not errors,
        "challenge": packet.get("challenge"),
        "input": str(packet_path),
        "requested_status": packet.get("requested_status"),
        "runner_track": packet.get("runner_track"),
        "promotion_ready": packet.get("promotion_ready"),
        "errors": errors,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
