#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.replay_request_guard import load_json, validate_request


ROOT = Path(__file__).resolve().parents[1]


def resolve(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a KernelForge trusted replay request.")
    parser.add_argument("--input", required=True, help="Replay request JSON.")
    parser.add_argument("--contract", default="verifier/replay-contract.json")
    parser.add_argument("--challenge", default="challenge.json")
    parser.add_argument("--schema-only", action="store_true", help="Validate schema without reading artifact files.")
    args = parser.parse_args()

    request_path = resolve(args.input)
    contract_path = resolve(args.contract)
    challenge_path = resolve(args.challenge)
    request = load_json(request_path)
    contract = load_json(contract_path)
    challenge = load_json(challenge_path)
    errors = validate_request(
        request,
        contract,
        root=ROOT,
        verify_files=not args.schema_only,
        challenge_contract=challenge,
    )
    report = {
        "ok": not errors,
        "challenge": request.get("challenge"),
        "input": str(request_path),
        "request_id": request.get("request_id"),
        "requested_status": request.get("requested_status"),
        "runner_track": request.get("runner_track"),
        "replay_ready": request.get("replay_ready"),
        "errors": errors,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
