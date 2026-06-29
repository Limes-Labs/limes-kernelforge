from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LimesLabsFixtureTests(unittest.TestCase):
    def test_leaderboard_fixture_is_candidate_only(self) -> None:
        payload = json.loads(
            (ROOT / "examples/limeslabs/leaderboard.example.json").read_text(encoding="utf-8")
        )
        self.assertEqual(payload["source"], "example-fixture")
        self.assertGreaterEqual(len(payload["entries"]), 1)
        for entry in payload["entries"]:
            self.assertEqual(entry["challenge"], "limes-kernelforge")
            self.assertEqual(entry["status"], "candidate")
            self.assertIsNone(entry["score"]["hidden_geomean_runtime_ms"])
            self.assertIn("reference_public_geomean_runtime_ms", entry["score"])
            self.assertIn("public_speedup_vs_reference", entry["score"])
            self.assertIn("public_runtime_delta_ms", entry["metrics"])
            self.assertIn("tolerance", entry["metrics"])
            self.assertIsNone(entry["replay"]["fixed_runner_track"])
            self.assertFalse(entry["replay"]["integration_audit"])

    def test_result_card_disclaims_verified_status(self) -> None:
        card = (ROOT / "examples/limeslabs/result-card.example.md").read_text(encoding="utf-8")
        self.assertIn("No fixed-runner replay has run", card)
        self.assertIn("must not be shown as", card)


if __name__ == "__main__":
    unittest.main()
