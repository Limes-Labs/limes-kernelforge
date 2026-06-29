from __future__ import annotations

import unittest

from harness.score import public_score


class PublicScoreTests(unittest.TestCase):
    def test_public_score_is_correct(self) -> None:
        score = public_score()
        self.assertTrue(score["correct"])
        self.assertLessEqual(score["max_abs_error"], 1e-9)
        self.assertLessEqual(score["max_rel_error"], 1e-9)
        self.assertGreater(score["public_geomean_runtime_ms"], 0.0)
        self.assertGreater(score["reference_public_geomean_runtime_ms"], 0.0)
        self.assertGreater(score["public_speedup_vs_reference"], 0.0)
        self.assertAlmostEqual(
            score["public_runtime_delta_ms"],
            score["public_geomean_runtime_ms"] - score["reference_public_geomean_runtime_ms"],
        )
        self.assertEqual(score["tolerance"], {"abs": 1e-9, "rel": 1e-9})

    def test_all_primitives_reported(self) -> None:
        score = public_score()
        self.assertEqual({"rmsnorm", "rope", "attention", "kv_decode"}, set(score["primitives"]))
        for primitive in score["primitives"].values():
            self.assertIn("reference_runtime_ms", primitive)
            self.assertIn("speedup_vs_reference", primitive)
            self.assertGreater(primitive["reference_runtime_ms"], 0.0)
            self.assertGreater(primitive["speedup_vs_reference"], 0.0)

    def test_public_score_does_not_publish_hidden_metrics(self) -> None:
        score = public_score()
        self.assertNotIn("hidden_geomean_runtime_ms", score)


if __name__ == "__main__":
    unittest.main()
