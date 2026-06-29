import json
import unittest
from pathlib import Path

from harness import reference
from harness.scoring import error_stats, score_cases
from solution import attention, kv_decode, rmsnorm, rope


ROOT = Path(__file__).resolve().parents[1]


class ReferenceAndSolutionTests(unittest.TestCase):
    def test_solution_matches_reference_on_public_cases(self):
        payload = json.loads(
            (ROOT / "cases/public_smoke/tiny_cases.json").read_text(encoding="utf-8")
        )
        for case in payload["tasks"]["rmsnorm"]:
            expected = reference.rmsnorm(**case["inputs"])
            actual = rmsnorm.rmsnorm(**case["inputs"])
            self.assertEqual(error_stats(actual, expected), (0.0, 0.0))
        for case in payload["tasks"]["rope"]:
            expected = reference.apply_rope(**case["inputs"])
            actual = rope.apply_rope(**case["inputs"])
            self.assertEqual(error_stats(actual, expected), (0.0, 0.0))
        for case in payload["tasks"]["causal_attention_prefill"]:
            expected = reference.causal_attention_prefill(**case["inputs"])
            actual = attention.causal_attention_prefill(**case["inputs"])
            self.assertEqual(error_stats(actual, expected), (0.0, 0.0))
        for case in payload["tasks"]["kv_decode_microcase"]:
            expected = reference.kv_decode(**case["inputs"])
            actual = kv_decode.kv_decode(**case["inputs"])
            self.assertEqual(error_stats(actual, expected), (0.0, 0.0))

    def test_public_score_payload_shape(self):
        payload = json.loads(
            (ROOT / "cases/public_smoke/tiny_cases.json").read_text(encoding="utf-8")
        )
        score = score_cases(payload, repeats=1)
        self.assertTrue(score["correct"])
        self.assertEqual(score["max_abs_error"], 0.0)
        self.assertEqual(score["max_rel_error"], 0.0)
        self.assertGreater(score["public_geomean_runtime_ms"], 0.0)
        self.assertGreater(score["reference_public_geomean_runtime_ms"], 0.0)
        self.assertGreater(score["public_speedup_vs_reference"], 0.0)
        self.assertAlmostEqual(
            score["public_runtime_delta_ms"],
            score["public_geomean_runtime_ms"] - score["reference_public_geomean_runtime_ms"],
        )
        self.assertEqual(score["tolerance"], {"abs": 1e-9, "rel": 1e-9})
        self.assertEqual(score["backend"], "python-stdlib")
        self.assertIn("python", score["hardware_fingerprint"])
        self.assertEqual(len(score["cases"]), 5)
        for case in score["cases"]:
            self.assertIn("reference_runtime_ms", case)
            self.assertIn("speedup_vs_reference", case)
            self.assertGreater(case["reference_runtime_ms"], 0.0)


if __name__ == "__main__":
    unittest.main()
