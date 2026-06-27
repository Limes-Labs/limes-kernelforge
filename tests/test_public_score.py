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

    def test_all_primitives_reported(self) -> None:
        score = public_score()
        self.assertEqual({"rmsnorm", "rope", "attention", "kv_decode"}, set(score["primitives"]))


if __name__ == "__main__":
    unittest.main()
