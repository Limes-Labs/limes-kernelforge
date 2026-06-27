import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ChallengeContractTests(unittest.TestCase):
    def test_required_contract_paths(self):
        contract = json.loads((ROOT / "challenge.json").read_text(encoding="utf-8"))
        self.assertEqual(contract["score"]["direction"], "minimize")
        self.assertEqual(
            contract["score"]["primaryMetric"], "public_geomean_runtime_ms"
        )
        self.assertEqual(
            contract["score"]["officialHiddenMetric"], "hidden_geomean_runtime_ms"
        )
        self.assertIn("solution/rmsnorm.py", contract["editablePaths"])
        for protected in [
            "harness/**",
            "cases/**",
            "hidden_cases/**",
            "challenge.json",
            "score.json",
            "leaderboard/**",
        ]:
            self.assertIn(protected, contract["forbiddenPaths"])

    def test_rules_document_protected_paths(self):
        rules = (ROOT / "RULES.md").read_text(encoding="utf-8")
        for protected in [
            "harness/**",
            "cases/**",
            "hidden_cases/**",
            "challenge.json",
            "score.json",
            "leaderboard/**",
        ]:
            self.assertIn(protected, rules)


if __name__ == "__main__":
    unittest.main()

