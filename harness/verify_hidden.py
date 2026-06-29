#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "verifier" / "replay-contract.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Describe the KernelForge hidden verifier contract.")
    parser.add_argument("--public-contract-only", action="store_true")
    args = parser.parse_args()
    if not args.public_contract_only:
        raise SystemExit("hidden verifier cases are not bundled; use --public-contract-only")
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    print(json.dumps(contract, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
