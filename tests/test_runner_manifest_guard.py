from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harness.runner_manifest_guard import load_json, validate_manifest


ROOT = Path(__file__).resolve().parents[1]


class RunnerManifestGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load_json(ROOT / "verifier/replay-contract.json")
        self.manifest = load_json(ROOT / "verifier/trusted-runner-manifest.example.json")

    def test_example_manifest_passes(self) -> None:
        self.assertEqual(validate_manifest(self.manifest, self.contract), [])

    def test_track_must_be_known(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["fixed_runner_tracks"][0]["id"] = "unknown-fixed"
        errors = validate_manifest(manifest, self.contract)
        self.assertTrue(any("known fixed runner track" in error for error in errors))

    def test_hidden_case_manifest_path_must_match_contract(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["hidden_case_manifest"]["path"] = "other/manifest.json"
        errors = validate_manifest(manifest, self.contract)
        self.assertTrue(any("hidden_case_manifest.path" in error for error in errors))

    def test_hidden_cases_must_not_be_bundled(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["hidden_case_manifest"]["hidden_cases_bundled"] = True
        errors = validate_manifest(manifest, self.contract)
        self.assertTrue(any("hidden_cases_bundled" in error for error in errors))

    def test_hidden_shapes_must_not_be_disclosed(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["anti_cheat"]["hidden_shapes_disclosed_before_candidate_freeze"] = True
        errors = validate_manifest(manifest, self.contract)
        self.assertTrue(any("hidden_shapes_disclosed" in error for error in errors))

    def test_timing_policy_must_match_contract(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["timing_policy"]["aggregation"] = "mean across all repetitions"
        errors = validate_manifest(manifest, self.contract)
        self.assertTrue(any("timing_policy.aggregation" in error for error in errors))

    def test_cli_accepts_example_manifest(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/validate_runner_manifest.py",
                "--input",
                "verifier/trusted-runner-manifest.example.json",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"ok": true', result.stdout)

    def test_cli_rejects_bad_manifest(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["anti_cheat"]["correctness_first"] = False
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_path = Path(temp_dir) / "bad-runner-manifest.json"
            bad_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/validate_runner_manifest.py",
                    "--input",
                    str(bad_path),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("correctness_first", result.stdout)


if __name__ == "__main__":
    unittest.main()
