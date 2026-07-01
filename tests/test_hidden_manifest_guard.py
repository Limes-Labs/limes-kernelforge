from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from harness.hidden_manifest_guard import load_json, validate_hidden_manifest


ROOT = Path(__file__).resolve().parents[1]


class HiddenManifestGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load_json(ROOT / "verifier/replay-contract.json")

    def test_example_hidden_manifest_validates(self) -> None:
        manifest = load_json(ROOT / "verifier/hidden-manifest.example.json")
        errors = validate_hidden_manifest(manifest, self.contract)
        self.assertEqual(errors, [])

    def test_rejects_candidate_disclosure(self) -> None:
        manifest = load_json(ROOT / "verifier/hidden-manifest.example.json")
        manifest["case_suites"][0]["disclosed_to_candidates"] = True
        errors = validate_hidden_manifest(manifest, self.contract)
        self.assertTrue(any("disclosed_to_candidates" in error for error in errors))

    def test_rejects_runner_track_drift(self) -> None:
        manifest = load_json(ROOT / "verifier/hidden-manifest.example.json")
        manifest["runner_tracks"] = [
            track for track in manifest["runner_tracks"] if track["id"] != "cuda-fixed"
        ]
        errors = validate_hidden_manifest(manifest, self.contract)
        self.assertTrue(any("runner_tracks" in error for error in errors))

    def test_rejects_placeholder_hash_for_real_manifest(self) -> None:
        manifest = load_json(ROOT / "verifier/hidden-manifest.example.json")
        manifest["source"] = "trusted-runner-local"
        manifest["hidden_manifest_ready"] = True
        errors = validate_hidden_manifest(manifest, self.contract)
        self.assertTrue(any("sha256" in error for error in errors))

    def test_accepts_real_manifest_shape(self) -> None:
        manifest = load_json(ROOT / "verifier/hidden-manifest.example.json")
        manifest["source"] = "trusted-runner-local"
        manifest["hidden_manifest_ready"] = True
        for index, suite in enumerate(manifest["case_suites"]):
            suite["case_count"] = 3 + index
            suite["sha256"] = f"{index + 1:064x}"
        for index, track in enumerate(manifest["runner_tracks"]):
            track["hardware_fingerprint_sha256"] = f"{index + 11:064x}"
        manifest["tolerance_matrix_hash"] = f"{21:064x}"
        manifest["timing_policy_hash"] = f"{22:064x}"
        errors = validate_hidden_manifest(manifest, self.contract)
        self.assertEqual(errors, [])

    def test_cli_validates_example(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/validate_hidden_manifest.py",
                "--input",
                "verifier/hidden-manifest.example.json",
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
