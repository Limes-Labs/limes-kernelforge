#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json


CONTRACT = {
    "hidden_verifier_ready": False,
    "mode": "public-contract-only",
    "official_primary_metric": "hidden_geomean_runtime_ms",
    "requires": [
        "hidden shape suite",
        "dtype-specific tolerance matrix",
        "fixed CPU, Apple Silicon/Metal, CUDA, and ROCm runner definitions",
        "warmup, repetition, and median timing policy",
        "memory caps",
        "native extension sandbox rules",
        "mini integration audit"
    ]
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Describe the KernelForge hidden verifier contract.")
    parser.add_argument("--public-contract-only", action="store_true")
    args = parser.parse_args()
    if not args.public_contract_only:
        raise SystemExit("hidden verifier cases are not bundled; use --public-contract-only")
    print(json.dumps(CONTRACT, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
