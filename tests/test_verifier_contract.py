from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class VerifierContractTests(unittest.TestCase):
    def load_contract(self) -> dict:
        return json.loads((ROOT / "verifier/replay-contract.json").read_text(encoding="utf-8"))

    def test_contract_pins_hidden_primary_metric_and_status_gates(self) -> None:
        contract = self.load_contract()
        self.assertEqual(contract["challenge"], "limes-kernelforge")
        self.assertFalse(contract["hidden_verifier_ready"])
        self.assertEqual(contract["official_primary_metric"], "hidden_geomean_runtime_ms")
        self.assertEqual(contract["score_direction"], "minimize")
        self.assertTrue(contract["correctness_first"])
        for status in ["candidate", "verified", "promoted", "replicated", "scaled"]:
            self.assertIn(status, contract["promotion_gates"])
            self.assertGreater(len(contract["promotion_gates"][status]), 0)

    def test_contract_defines_fixed_runner_tracks_and_private_hidden_cases(self) -> None:
        contract = self.load_contract()
        tracks = {track["id"] for track in contract["runner_tracks"]}
        self.assertEqual(
            tracks,
            {"cpu-fixed", "apple-metal-fixed", "cuda-fixed", "rocm-fixed"},
        )
        self.assertFalse(contract["hidden_case_policy"]["hidden_cases_bundled"])
        self.assertEqual(
            contract["hidden_case_policy"]["public_schema_example_path"],
            "verifier/hidden-manifest.example.json",
        )
        self.assertFalse(contract["hidden_case_policy"]["candidate_selection_uses_hidden_cases"])
        self.assertEqual(contract["trusted_runner"]["network"], "disabled during official scoring")

    def test_contract_defines_trusted_replay_request_policy(self) -> None:
        policy = self.load_contract()["trusted_replay_request_policy"]
        self.assertEqual(policy["request_template_path"], "templates/replay-request.example.json")
        self.assertEqual(policy["requested_status"], "verified")
        self.assertTrue(policy["runner_track_required"])
        self.assertFalse(policy["hidden_feedback_for_candidate_selection"])
        self.assertFalse(policy["fixed_runner_feedback_before_candidate_freeze"])
        self.assertEqual(policy["max_trusted_replays_per_submission"], 1)

    def test_contract_defines_tolerance_matrix_and_result_fields(self) -> None:
        contract = self.load_contract()
        for dtype in ["float64", "float32", "float16", "bfloat16"]:
            self.assertIn(dtype, contract["tolerance_matrix"])
            self.assertIn("abs", contract["tolerance_matrix"][dtype])
            self.assertIn("rel", contract["tolerance_matrix"][dtype])
        metrics = set(contract["official_result_schema"]["metrics"])
        for required in {
            "hidden_geomean_runtime_ms",
            "reference_hidden_geomean_runtime_ms",
            "hidden_speedup_vs_reference",
            "runner_track",
            "case_suite_hash",
            "integration_audit",
        }:
            self.assertIn(required, metrics)

    def test_verify_hidden_prints_contract(self) -> None:
        result = subprocess.run(
            [sys.executable, "harness/verify_hidden.py", "--public-contract-only"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["challenge"], "limes-kernelforge")
        self.assertEqual(payload["official_primary_metric"], "hidden_geomean_runtime_ms")


if __name__ == "__main__":
    unittest.main()
