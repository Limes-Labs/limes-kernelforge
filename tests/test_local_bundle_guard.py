from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harness.invariant_probes import run_invariant_probes
from harness.local_bundle_guard import validate_local_bundle
from harness.score import public_score
from harness.submission_guard import load_json
from tests.test_submission_guard import valid_manifest


ROOT = Path(__file__).resolve().parents[1]


def current_manifest_and_ledger() -> tuple[dict, dict]:
    score = public_score()
    probes = run_invariant_probes()
    manifest = valid_manifest()
    manifest["public_score"].update(score)
    manifest["invariant_probes"] = probes

    ledger = json.loads((ROOT / "templates/search-ledger.example.json").read_text(encoding="utf-8"))
    selected = next(attempt for attempt in ledger["attempts"] if attempt["status"] == "selected")
    selected["correct"] = score["correct"]
    selected["public_stress_correct"] = score["public_stress_correct"]
    selected["backend"] = score["backend"]
    selected["invariant_probes_passed"] = probes["ok"]
    return manifest, ledger


class LocalBundleGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load_json(ROOT / "challenge.json")

    def test_accepts_current_correctness_probe_and_ledger_bundle(self) -> None:
        manifest, ledger = current_manifest_and_ledger()
        report = validate_local_bundle(
            manifest=manifest,
            contract=self.contract,
            changed_paths=["solution/rmsnorm.py"],
            search_ledger=ledger,
        )
        self.assertTrue(report["ok"], report["errors"])

    def test_rejects_stale_public_error_metric(self) -> None:
        manifest, ledger = current_manifest_and_ledger()
        manifest["public_score"]["max_abs_error"] = 123.0
        report = validate_local_bundle(
            manifest=manifest,
            contract=self.contract,
            changed_paths=["solution/rmsnorm.py"],
            search_ledger=ledger,
        )
        self.assertFalse(report["ok"])
        self.assertTrue(any("public_score.max_abs_error" in error for error in report["errors"]))

    def test_cli_accepts_current_bundle_with_explicit_changed_file(self) -> None:
        manifest, ledger = current_manifest_and_ledger()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            ledger_path = temp / "search-ledger.json"
            manifest_path = temp / "submission.json"
            manifest["search_ledger"]["path"] = str(ledger_path)
            ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/validate_local_bundle.py",
                    "--manifest",
                    str(manifest_path),
                    "--changed-file",
                    "solution/rmsnorm.py",
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
