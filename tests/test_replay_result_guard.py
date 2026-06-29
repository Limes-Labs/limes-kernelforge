from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harness.replay_result_guard import load_json, validate_result


ROOT = Path(__file__).resolve().parents[1]


class ReplayResultGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load_json(ROOT / "verifier/replay-contract.json")
        self.result = load_json(ROOT / "templates/replay-result.example.json")

    def test_example_replay_result_passes(self) -> None:
        self.assertEqual(validate_result(self.result, self.contract), [])

    def test_score_must_match_hidden_runtime(self) -> None:
        result = copy.deepcopy(self.result)
        result["score"] = result["metrics"]["hidden_geomean_runtime_ms"] + 1.0
        errors = validate_result(result, self.contract)
        self.assertTrue(any("score must equal" in error for error in errors))

    def test_runner_track_must_be_known(self) -> None:
        result = copy.deepcopy(self.result)
        result["metrics"]["runner_track"] = "unknown-fixed-runner"
        result["replay"]["fixed_runner_track"] = "unknown-fixed-runner"
        errors = validate_result(result, self.contract)
        self.assertTrue(any("known fixed runner track" in error for error in errors))

    def test_promoted_result_requires_result_card_and_promotable(self) -> None:
        result = copy.deepcopy(self.result)
        result["status"] = "promoted"
        result["promotion"]["promotable"] = False
        result["links"]["result_card"] = None
        errors = validate_result(result, self.contract)
        self.assertTrue(any("promotable" in error for error in errors))
        self.assertTrue(any("result_card" in error for error in errors))

    def test_scaled_result_requires_integration_audit(self) -> None:
        result = copy.deepcopy(self.result)
        result["status"] = "scaled"
        result["promotion"]["promotable"] = True
        result["links"]["result_card"] = "https://limeslabs.eu/limes-kernelforge/example"
        result["promotion"]["integration_audit"] = False
        result["metrics"]["integration_audit"] = False
        errors = validate_result(result, self.contract)
        self.assertTrue(any("promotion.integration_audit" in error for error in errors))
        self.assertTrue(any("metrics.integration_audit" in error for error in errors))

    def test_cli_accepts_example_replay_result(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/validate_replay_result.py",
                "--input",
                "templates/replay-result.example.json",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"ok": true', result.stdout)

    def test_cli_rejects_bad_replay_result(self) -> None:
        result_payload = copy.deepcopy(self.result)
        result_payload["replay"]["clean_checkout"] = False
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_path = Path(temp_dir) / "bad-replay-result.json"
            bad_path.write_text(json.dumps(result_payload), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/validate_replay_result.py",
                    "--input",
                    str(bad_path),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("clean_checkout", result.stdout)


if __name__ == "__main__":
    unittest.main()
