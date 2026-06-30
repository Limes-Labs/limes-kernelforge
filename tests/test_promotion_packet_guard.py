from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harness.promotion_packet_guard import load_json, validate_packet


ROOT = Path(__file__).resolve().parents[1]


class PromotionPacketGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load_json(ROOT / "verifier/replay-contract.json")
        self.packet = load_json(ROOT / "templates/promotion-packet.example.json")

    def test_example_promotion_packet_passes(self) -> None:
        self.assertEqual(validate_packet(self.packet, self.contract), [])

    def test_runner_track_must_be_known(self) -> None:
        packet = copy.deepcopy(self.packet)
        packet["runner_track"] = "unknown-track"
        errors = validate_packet(packet, self.contract)
        self.assertTrue(any("known fixed runner track" in error for error in errors))

    def test_promoted_packet_requires_memory_and_invalid_optimization_audits(self) -> None:
        packet = copy.deepcopy(self.packet)
        packet["source"] = "trusted-runner"
        packet["requested_status"] = "promoted"
        packet["promotion_ready"] = True
        packet["evidence"]["result_card_present"] = True
        errors = validate_packet(packet, self.contract)
        self.assertTrue(any("memory_cap_respected" in error for error in errors))
        self.assertTrue(any("invalid_optimization_audit" in error for error in errors))
        self.assertTrue(any("review.decision must be approve" in error for error in errors))

    def test_promoted_packet_can_pass_when_all_gates_are_bound(self) -> None:
        packet = copy.deepcopy(self.packet)
        packet["source"] = "trusted-runner"
        packet.pop("disclaimer", None)
        packet["requested_status"] = "promoted"
        packet["promotion_ready"] = True
        packet["evidence"]["memory_cap_respected"] = True
        packet["evidence"]["invalid_optimization_audit"] = True
        packet["evidence"]["result_card_present"] = True
        packet["gates"]["passed"] = ["hidden correctness", "fixed runner timing", "invalid optimization audit"]
        packet["gates"]["failed"] = []
        packet["gates"]["blocked"] = []
        packet["review"]["decision"] = "approve"
        errors = validate_packet(packet, self.contract)
        self.assertEqual(errors, [])

    def test_scaled_packet_requires_integration_audit(self) -> None:
        packet = copy.deepcopy(self.packet)
        packet["source"] = "trusted-runner"
        packet["requested_status"] = "scaled"
        packet["promotion_ready"] = True
        packet["evidence"]["memory_cap_respected"] = True
        packet["evidence"]["invalid_optimization_audit"] = True
        packet["evidence"]["result_card_present"] = True
        packet["gates"]["passed"] = ["hidden correctness", "fixed runner timing", "scaled hidden shapes"]
        packet["gates"]["failed"] = []
        packet["gates"]["blocked"] = []
        packet["review"]["decision"] = "approve"
        errors = validate_packet(packet, self.contract)
        self.assertTrue(any("integration_audit" in error for error in errors))
        self.assertTrue(any("scaled_audit" in error for error in errors))

    def test_cli_accepts_example_packet(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/validate_promotion_packet.py",
                "--input",
                "templates/promotion-packet.example.json",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"ok": true', result.stdout)

    def test_cli_rejects_bad_packet(self) -> None:
        packet = copy.deepcopy(self.packet)
        packet["evidence"]["correctness_passed"] = False
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_path = Path(temp_dir) / "bad-promotion-packet.json"
            bad_path.write_text(json.dumps(packet), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/validate_promotion_packet.py",
                    "--input",
                    str(bad_path),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("correctness_passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
