#!/usr/bin/env bash
set -euo pipefail

python3 harness/score.py --output score.json
python3 -m unittest discover -s tests
