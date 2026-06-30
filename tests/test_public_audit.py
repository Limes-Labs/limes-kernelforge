from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harness.public_audit import run_public_audit, scan_forbidden_static_patterns


ROOT = Path(__file__).resolve().parents[1]


class PublicAuditTests(unittest.TestCase):
    def test_default_solution_passes_public_audit(self) -> None:
        report = run_public_audit()
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["audit_count"], 5)
        self.assertEqual(
            {
                "solution_static_boundary",
                "rmsnorm_sign_symmetry",
                "rope_identity_and_pair_norm",
                "attention_value_shift_invariance",
                "kv_decode_value_shift_invariance",
            },
            {audit["name"] for audit in report["audits"]},
        )

    def test_static_boundary_scan_flags_case_reads(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "candidate.py"
            path.write_text("open('cases/public_smoke/cases.json')\n", encoding="utf-8")
            errors = scan_forbidden_static_patterns([path])
        self.assertTrue(any("cases/public_smoke" in error for error in errors), errors)

    def test_cli_accepts_default_solution(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/run_public_audit.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"ok": true', result.stdout)


if __name__ == "__main__":
    unittest.main()
