from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TaskSpecTests(unittest.TestCase):
    def setUp(self) -> None:
        self.challenge = json.loads((ROOT / "challenge.json").read_text(encoding="utf-8"))
        self.contract = json.loads((ROOT / "verifier/replay-contract.json").read_text(encoding="utf-8"))
        self.spec = json.loads((ROOT / self.contract["task_spec_path"]).read_text(encoding="utf-8"))

    def test_task_spec_matches_challenge(self) -> None:
        self.assertEqual(self.spec["challenge"], self.challenge["id"])
        self.assertTrue(self.spec["public_surface"]["candidate_only"])
        self.assertEqual(self.spec["public_surface"]["official_metric"], self.challenge["score"]["primaryMetric"])

    def test_every_primitive_points_to_editable_file_and_declares_hidden_axes(self) -> None:
        editable = set(self.challenge["editablePaths"])
        primitive_ids = {primitive["id"] for primitive in self.spec["primitives"]}
        self.assertEqual(primitive_ids, {"rmsnorm", "rope", "attention", "kv_decode"})
        for primitive in self.spec["primitives"]:
            with self.subTest(primitive=primitive["id"]):
                self.assertIn(primitive["editable_file"], editable)
                self.assertTrue((ROOT / primitive["editable_file"]).exists())
                self.assertTrue(primitive["reference_function"].startswith("harness.reference."))
                self.assertGreaterEqual(len(primitive["correctness_invariants"]), 3)
                self.assertGreaterEqual(len(primitive["hidden_replay_axes"]), 3)
                self.assertGreaterEqual(len(primitive["invalid_patterns"]), 2)

    def test_official_replay_axes_record_hashes_speed_and_integration(self) -> None:
        axes = {axis["id"]: axis for axis in self.spec["official_replay_axes"]}
        self.assertIn("hidden-correctness", axes)
        self.assertIn("fixed-runner-timing", axes)
        self.assertIn("integration-audit", axes)
        self.assertIn("case_suite_hash", axes["hidden-correctness"]["must_record"])
        self.assertIn("hidden_geomean_runtime_ms", axes["fixed-runner-timing"]["must_record"])
        self.assertIn("integration_audit", axes["integration-audit"]["must_record"])


if __name__ == "__main__":
    unittest.main()
