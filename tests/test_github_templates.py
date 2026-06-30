from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class GitHubTemplateTests(unittest.TestCase):
    def test_submission_form_names_protected_surface_and_replay_gates(self) -> None:
        form = (ROOT / ".github/ISSUE_TEMPLATE/submission.yml").read_text(encoding="utf-8")
        for phrase in [
            "verifier/**",
            "verifier/task-spec.json",
            "scripts/check_submission.py",
            "scripts/validate_agent_notes.py",
            "scripts/validate_replay_result.py",
            "scripts/validate_promotion_packet.py",
            "candidate only",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, form)

    def test_pull_request_template_keeps_validation_commands_visible(self) -> None:
        template = (ROOT / ".github/pull_request_template.md").read_text(encoding="utf-8")
        for phrase in [
            "verifier/**",
            "verifier/task-spec.json",
            "templates/agent-notes.example.json",
            "templates/replay-result.example.json",
            "templates/promotion-packet.example.json",
            "verifier/trusted-runner-manifest.example.json",
            "verifier/baseline-record.example.json",
            "git diff --check",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, template)


if __name__ == "__main__":
    unittest.main()
