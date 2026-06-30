from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harness.search_ledger_guard import load_json, validate_ledger


ROOT = Path(__file__).resolve().parents[1]


class SearchLedgerGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ledger = load_json(ROOT / "templates/search-ledger.example.json")

    def test_example_search_ledger_passes(self) -> None:
        self.assertEqual(validate_ledger(self.ledger), [])

    def test_rejects_fixed_runner_feedback_before_replay(self) -> None:
        ledger = copy.deepcopy(self.ledger)
        ledger["search_budget"]["fixed_runner_feedback_used"] = True
        errors = validate_ledger(ledger)
        self.assertTrue(any("fixed_runner_feedback_used" in error for error in errors))

    def test_selected_attempt_must_pass_stress_and_invariants(self) -> None:
        ledger = copy.deepcopy(self.ledger)
        ledger["attempts"][1]["public_stress_correct"] = False
        ledger["attempts"][1]["invariant_probes_passed"] = False
        errors = validate_ledger(ledger)
        self.assertTrue(any("public stress" in error for error in errors))
        self.assertTrue(any("invariant probes" in error for error in errors))

    def test_selected_score_must_match_selected_attempt(self) -> None:
        ledger = copy.deepcopy(self.ledger)
        ledger["candidate_selection"]["selected_score"] = 1.0
        errors = validate_ledger(ledger)
        self.assertTrue(any("selected_score" in error for error in errors))

    def test_cli_accepts_example_ledger(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/validate_search_ledger.py",
                "--input",
                "templates/search-ledger.example.json",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"ok": true', result.stdout)

    def test_cli_rejects_bad_ledger(self) -> None:
        ledger = copy.deepcopy(self.ledger)
        ledger["public_data_boundary"]["used_hidden_cases"] = True
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_path = Path(temp_dir) / "bad-search-ledger.json"
            bad_path.write_text(json.dumps(ledger), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/validate_search_ledger.py",
                    "--input",
                    str(bad_path),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("used_hidden_cases", result.stdout)


if __name__ == "__main__":
    unittest.main()
