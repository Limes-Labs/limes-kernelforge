import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TemplateTests(unittest.TestCase):
    def test_json_templates_parse(self):
        for relative in [
            "templates/submission.json",
            "templates/leaderboard-entry.json",
            "templates/agent-notes.example.json",
            "templates/replay-result.example.json",
            "verifier/task-spec.json",
            "verifier/trusted-runner-manifest.example.json",
            "verifier/baseline-record.example.json",
            "cases/public_smoke/tiny_cases.json",
            "challenge.json",
        ]:
            with self.subTest(relative=relative):
                payload = json.loads((ROOT / relative).read_text(encoding="utf-8"))
                self.assertIsInstance(payload, dict)

    def test_result_card_mentions_promotion_gates(self):
        card = (ROOT / "templates/result-card.md").read_text(encoding="utf-8")
        for phrase in [
            "Hidden correctness",
            "Fixed-runner timing",
            "Mini inference/training-loop integration",
        ]:
            self.assertIn(phrase, card)


if __name__ == "__main__":
    unittest.main()
