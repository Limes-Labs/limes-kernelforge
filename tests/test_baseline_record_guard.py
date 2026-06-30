from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harness.baseline_record_guard import load_json, validate_record


ROOT = Path(__file__).resolve().parents[1]


class BaselineRecordGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load_json(ROOT / "verifier/replay-contract.json")
        self.record = load_json(ROOT / "verifier/baseline-record.example.json")

    def test_example_baseline_record_passes(self) -> None:
        self.assertEqual(validate_record(self.record, self.contract), [])

    def test_runner_track_must_be_known(self) -> None:
        record = copy.deepcopy(self.record)
        record["runner_track"] = "unknown-fixed"
        record["promotion_use"]["runner_track"] = "unknown-fixed"
        errors = validate_record(record, self.contract)
        self.assertTrue(any("known fixed runner track" in error for error in errors))

    def test_geomean_must_match_case_results(self) -> None:
        record = copy.deepcopy(self.record)
        record["aggregate"]["reference_hidden_geomean_runtime_ms"] = 0.001
        errors = validate_record(record, self.contract)
        self.assertTrue(any("geomean case runtime" in error for error in errors))

    def test_all_case_results_must_be_correct(self) -> None:
        record = copy.deepcopy(self.record)
        record["case_results"][0]["correct"] = False
        errors = validate_record(record, self.contract)
        self.assertTrue(any("correct must be true" in error for error in errors))

    def test_promoted_comparison_requires_frozen_baseline(self) -> None:
        record = copy.deepcopy(self.record)
        record["promotion_use"]["used_for_promoted_comparison"] = True
        errors = validate_record(record, self.contract)
        self.assertTrue(any("baseline_status frozen" in error for error in errors))

    def test_hidden_shapes_must_not_be_disclosed(self) -> None:
        record = copy.deepcopy(self.record)
        record["replay_constraints"]["hidden_shapes_disclosed_before_candidate_freeze"] = True
        errors = validate_record(record, self.contract)
        self.assertTrue(any("hidden_shapes_disclosed" in error for error in errors))

    def test_cli_accepts_example_record(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/validate_baseline_record.py",
                "--input",
                "verifier/baseline-record.example.json",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"ok": true', result.stdout)

    def test_cli_rejects_bad_record(self) -> None:
        record = copy.deepcopy(self.record)
        record["aggregate"]["correct"] = False
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_path = Path(temp_dir) / "bad-baseline-record.json"
            bad_path.write_text(json.dumps(record), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/validate_baseline_record.py",
                    "--input",
                    str(bad_path),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("aggregate.correct", result.stdout)


if __name__ == "__main__":
    unittest.main()
