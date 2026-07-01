from __future__ import annotations

import copy
import subprocess
import sys
import unittest
from pathlib import Path

from harness.public_baseline_guard import DEFAULT_BASELINE, load_json, validate_public_baseline


ROOT = Path(__file__).resolve().parents[1]


class PublicBaselineGuardTests(unittest.TestCase):
    def test_locked_public_baseline_matches_current_smoke_contract(self) -> None:
        report = validate_public_baseline(load_json(DEFAULT_BASELINE))
        self.assertTrue(report["ok"], report["errors"])

    def test_drifted_score_field_fails(self) -> None:
        baseline = load_json(DEFAULT_BASELINE)
        drifted = copy.deepcopy(baseline)
        drifted["score_fields"]["max_abs_error"] = 123.0
        report = validate_public_baseline(drifted)
        self.assertFalse(report["ok"])
        self.assertTrue(any("max_abs_error" in error for error in report["errors"]))

    def test_cli_accepts_locked_baseline(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/check_public_baseline.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"ok": true', result.stdout)


if __name__ == "__main__":
    unittest.main()
