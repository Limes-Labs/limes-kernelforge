#!/usr/bin/env bash
set -euo pipefail

python3 harness/score.py --output score.json
python3 scripts/run_invariant_probes.py
python3 -m unittest discover -s tests
