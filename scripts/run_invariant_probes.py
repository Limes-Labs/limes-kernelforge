#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.invariant_probes import dumps_report, run_invariant_probes


def main() -> int:
    report = run_invariant_probes()
    print(dumps_report(report), end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
