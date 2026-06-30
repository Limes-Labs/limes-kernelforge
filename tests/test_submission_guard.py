from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harness.submission_guard import (
    REQUIRED_PUBLIC_SCORE_FIELDS,
    classify_changed_paths,
    load_json,
    validate_manifest,
    validate_submission,
)


ROOT = Path(__file__).resolve().parents[1]


def valid_manifest() -> dict:
    public_score = {field: 1 for field in REQUIRED_PUBLIC_SCORE_FIELDS}
    public_score.update(
        {
            "correct": True,
            "backend": "python-stdlib",
            "tolerance": {"abs": 1e-9, "rel": 1e-9},
        }
    )
    return {
        "challenge": "limes-kernelforge",
        "status": "candidate",
        "commit": "0123456789abcdef0123456789abcdef01234567",
        "changed_files": ["solution/rmsnorm.py"],
        "primitives": ["rmsnorm"],
        "public_score": public_score,
        "hardware_fingerprint": "local test machine",
        "native_extension": False,
        "method_summary": "Use a clearer loop ordering for the RMSNorm public path.",
        "expected_failure_modes": ["May not improve hidden vector dimensions."],
        "agent_notes": "tests only",
    }


class SubmissionGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load_json(ROOT / "challenge.json")

    def test_classifies_editable_forbidden_and_unknown_paths(self) -> None:
        classified = classify_changed_paths(
            ["solution/rmsnorm.py", "cases/public_smoke/cases.json", "verifier/task-spec.json", "README.md"],
            self.contract,
        )
        self.assertEqual(classified["editable"], ["solution/rmsnorm.py"])
        self.assertEqual(classified["forbidden"], ["cases/public_smoke/cases.json", "verifier/task-spec.json"])
        self.assertEqual(classified["unknown"], ["README.md"])

    def test_valid_manifest_passes(self) -> None:
        errors = validate_manifest(valid_manifest(), self.contract)
        self.assertEqual(errors, [])

    def test_incorrect_public_score_fails(self) -> None:
        manifest = valid_manifest()
        manifest["public_score"]["correct"] = False
        errors = validate_manifest(manifest, self.contract)
        self.assertTrue(any("public_score.correct" in error for error in errors))

    def test_unknown_primitive_fails(self) -> None:
        manifest = valid_manifest()
        manifest["primitives"] = ["rmsnorm", "made_up_kernel"]
        errors = validate_manifest(manifest, self.contract)
        self.assertTrue(any("unknown entries" in error for error in errors))

    def test_checked_diff_must_match_manifest(self) -> None:
        errors = validate_submission(
            valid_manifest(),
            self.contract,
            ["solution/rmsnorm.py", "solution/rope.py"],
        )
        self.assertTrue(any("exactly match" in error for error in errors))

    def test_cli_accepts_explicit_changed_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "submission.json"
            manifest_path.write_text(json.dumps(valid_manifest()), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/check_submission.py",
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
