from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ContractTests(unittest.TestCase):
    def test_challenge_lists_required_protected_paths(self) -> None:
        challenge = json.loads((ROOT / "challenge.json").read_text(encoding="utf-8"))
        verifier = json.loads((ROOT / "verifier/replay-contract.json").read_text(encoding="utf-8"))
        forbidden = set(challenge["forbiddenPaths"])
        for required in {
            "harness/**",
            "cases/**",
            "verifier/**",
            "hidden_cases/**",
            "challenge.json",
            "score.json",
            "leaderboard/**",
        }:
            self.assertIn(required, forbidden)
        self.assertIn("audit", challenge["commands"])
        self.assertIn("scripts/check_submission.py", challenge["commands"]["audit"])
        self.assertIn("validateLeaderboard", challenge["commands"])
        self.assertIn("scripts/validate_leaderboard.py", challenge["commands"]["validateLeaderboard"])
        self.assertIn("validateAgentNotes", challenge["commands"])
        self.assertIn("scripts/validate_agent_notes.py", challenge["commands"]["validateAgentNotes"])
        self.assertIn("validateReplayResult", challenge["commands"])
        self.assertIn("scripts/validate_replay_result.py", challenge["commands"]["validateReplayResult"])
        self.assertEqual(verifier["challenge"], challenge["id"])
        self.assertEqual(verifier["task_spec_path"], "verifier/task-spec.json")
        self.assertEqual(verifier["official_primary_metric"], challenge["score"]["primaryMetric"])
        self.assertEqual(verifier["protected_surface"]["editable_paths"], challenge["editablePaths"])
        self.assertEqual(verifier["protected_surface"]["forbidden_paths"], challenge["forbiddenPaths"])

    def test_templates_are_valid_json(self) -> None:
        for path in (ROOT / "templates").glob("*.json"):
            with self.subTest(path=path.name):
                json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
