from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from harness.replay_request_guard import load_json, validate_request


ROOT = Path(__file__).resolve().parents[1]


class ReplayRequestGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load_json(ROOT / "verifier/replay-contract.json")

    def test_example_replay_request_validates(self) -> None:
        request = load_json(ROOT / "templates/replay-request.example.json")
        errors = validate_request(request, self.contract, verify_files=False)
        self.assertEqual(errors, [])

    def test_rejects_hidden_feedback_request(self) -> None:
        request = load_json(ROOT / "templates/replay-request.example.json")
        request["anti_probing"]["hidden_feedback_requested"] = True
        errors = validate_request(request, self.contract, verify_files=False)
        self.assertTrue(any("hidden_feedback_requested" in error for error in errors))

    def test_rejects_unknown_runner_track(self) -> None:
        request = load_json(ROOT / "templates/replay-request.example.json")
        request["runner_track"] = "unlisted-gpu"
        errors = validate_request(request, self.contract, verify_files=False)
        self.assertTrue(any("runner_track" in error for error in errors))

    def test_rejects_fixed_runner_feedback_before_freeze(self) -> None:
        request = load_json(ROOT / "templates/replay-request.example.json")
        request["anti_probing"]["fixed_runner_feedback_before_candidate_freeze"] = True
        errors = validate_request(request, self.contract, verify_files=False)
        self.assertTrue(any("fixed_runner_feedback_before_candidate_freeze" in error for error in errors))

    def test_ready_request_requires_approval(self) -> None:
        request = load_json(ROOT / "templates/replay-request.example.json")
        request["source"] = "maintainer-review"
        request["replay_ready"] = True
        request["review"]["decision"] = "hold"
        errors = validate_request(request, self.contract, verify_files=False)
        self.assertTrue(any("review.decision" in error for error in errors))

    def test_cli_validates_example(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/validate_replay_request.py",
                "--input",
                "templates/replay-request.example.json",
                "--schema-only",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"ok": true', result.stdout)


if __name__ == "__main__":
    unittest.main()
