from __future__ import annotations

import json
import unittest
from pathlib import Path

from harness import reference
from harness.scoring import score_cases


ROOT = Path(__file__).resolve().parents[1]


class StressCaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = json.loads(
            (ROOT / "cases/public_smoke/stress_cases.json").read_text(encoding="utf-8")
        )

    def test_stress_cases_cover_all_primitives(self) -> None:
        self.assertEqual(
            {"rmsnorm", "rope", "causal_attention_prefill", "kv_decode_microcase"},
            set(self.payload["tasks"]),
        )
        self.assertGreaterEqual(sum(len(cases) for cases in self.payload["tasks"].values()), 4)

    def test_stress_cases_match_reference(self) -> None:
        score = score_cases(self.payload, repeats=1)
        self.assertTrue(score["correct"])
        self.assertEqual(score["max_abs_error"], 0.0)
        self.assertEqual(score["max_rel_error"], 0.0)
        self.assertEqual(len(score["cases"]), 4)

    def test_causal_stress_case_blocks_future_value_leakage(self) -> None:
        case = self.payload["tasks"]["causal_attention_prefill"][0]
        output = reference.causal_attention_prefill(**case["inputs"])
        self.assertEqual(output[0], [3.0, -1.0])
        self.assertLess(output[1][0], 5.0)
        self.assertGreater(output[2][0], 900.0)


if __name__ == "__main__":
    unittest.main()
