from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harness.source_bundle_guard import build_source_bundle, validate_source_bundle
from harness.submission_guard import load_json


ROOT = Path(__file__).resolve().parents[1]


class SourceBundleGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load_json(ROOT / "challenge.json")
        self.commit = "0123456789abcdef0123456789abcdef01234567"

    def test_builds_and_validates_editable_bundle(self) -> None:
        report = build_source_bundle(
            contract=self.contract,
            changed_paths=["solution/rmsnorm.py"],
            source_commit=self.commit,
        )
        self.assertTrue(report["ok"], report["errors"])
        bundle = report["bundle"]
        self.assertEqual(bundle["challenge"], "limes-kernelforge")
        self.assertEqual(bundle["changed_files"], ["solution/rmsnorm.py"])
        self.assertEqual(len(bundle["bundle_sha256"]), 64)

        validation = validate_source_bundle(bundle, self.contract)
        self.assertTrue(validation["ok"], validation["errors"])

    def test_rejects_forbidden_file(self) -> None:
        report = build_source_bundle(
            contract=self.contract,
            changed_paths=["cases/public_smoke/cases.json"],
            source_commit=self.commit,
        )
        self.assertFalse(report["ok"])
        self.assertTrue(any("forbidden files changed" in error for error in report["errors"]))

    def test_rejects_stale_hash(self) -> None:
        report = build_source_bundle(
            contract=self.contract,
            changed_paths=["solution/rmsnorm.py"],
            source_commit=self.commit,
        )
        bundle = json.loads(json.dumps(report["bundle"]))
        bundle["files"][0]["sha256"] = "0" * 64
        validation = validate_source_bundle(bundle, self.contract)
        self.assertFalse(validation["ok"])
        self.assertTrue(any("stale" in error for error in validation["errors"]))

    def test_cli_builds_then_validates_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_path = Path(temp_dir) / "submission-bundle.json"
            build = subprocess.run(
                [
                    sys.executable,
                    "scripts/build_submission_bundle.py",
                    "--changed-file",
                    "solution/rmsnorm.py",
                    "--commit",
                    self.commit,
                    "--output",
                    str(bundle_path),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            validate = subprocess.run(
                [
                    sys.executable,
                    "scripts/validate_submission_bundle.py",
                    "--input",
                    str(bundle_path),
                    "--commit",
                    self.commit,
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(validate.returncode, 0, validate.stdout + validate.stderr)
        self.assertIn('"ok": true', validate.stdout)


if __name__ == "__main__":
    unittest.main()
