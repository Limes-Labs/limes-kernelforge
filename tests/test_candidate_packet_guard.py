from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harness.agent_notes_guard import load_json as load_notes_json
from harness.candidate_packet_guard import build_candidate_packet, validate_packet
from harness.invariant_probes import run_invariant_probes
from harness.public_audit import run_public_audit
from harness.score import public_score
from harness.submission_guard import load_json
from tests.test_local_bundle_guard import current_manifest_ledger_and_bundle


ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class CandidatePacketGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load_json(ROOT / "challenge.json")

    def test_schema_only_example_validates_without_artifact_files(self) -> None:
        packet = load_json(ROOT / "templates/candidate-packet.example.json")
        errors = validate_packet(packet, self.contract, verify_files=False)
        self.assertEqual(errors, [])

    def test_builds_and_validates_real_local_packet(self) -> None:
        manifest, ledger, source_bundle = current_manifest_ledger_and_bundle()
        score = public_score()
        probes = run_invariant_probes()
        audit = run_public_audit()
        notes = load_notes_json(ROOT / "templates/agent-notes.example.json")
        manifest["source_bundle"]["bundle_sha256"] = source_bundle["bundle_sha256"]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            manifest_path = temp / "submission.json"
            bundle_path = temp / "submission-bundle.json"
            ledger_path = temp / "search-ledger.json"
            notes_path = temp / "agent-notes.json"
            score_path = temp / "score.json"
            probes_path = temp / "invariant-probes.json"
            audit_path = temp / "public-audit.json"
            for path, payload in [
                (manifest_path, manifest),
                (bundle_path, source_bundle),
                (ledger_path, ledger),
                (notes_path, notes),
                (score_path, score),
                (probes_path, probes),
                (audit_path, audit),
            ]:
                write_json(path, payload)

            packet = build_candidate_packet(
                contract=self.contract,
                manifest_path=manifest_path,
                source_bundle_path=bundle_path,
                search_ledger_path=ledger_path,
                agent_notes_path=notes_path,
                public_score_path=score_path,
                invariant_probes_path=probes_path,
                public_audit_path=audit_path,
                packet_id="unit-test-candidate",
            )
            packet_path = temp / "candidate-packet.json"
            write_json(packet_path, packet)

            self.assertTrue(packet["candidate_ready"], packet["gates"])
            errors = validate_packet(packet, self.contract)
            self.assertEqual(errors, [])

            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/validate_candidate_packet.py",
                    "--input",
                    str(packet_path),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"ok": true', result.stdout)

    def test_rejects_tampered_artifact_hash(self) -> None:
        manifest, ledger, source_bundle = current_manifest_ledger_and_bundle()
        score = public_score()
        probes = run_invariant_probes()
        audit = run_public_audit()
        notes = load_notes_json(ROOT / "templates/agent-notes.example.json")
        manifest["source_bundle"]["bundle_sha256"] = source_bundle["bundle_sha256"]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            paths = {
                "manifest": temp / "submission.json",
                "bundle": temp / "submission-bundle.json",
                "ledger": temp / "search-ledger.json",
                "notes": temp / "agent-notes.json",
                "score": temp / "score.json",
                "probes": temp / "invariant-probes.json",
                "audit": temp / "public-audit.json",
            }
            for path, payload in [
                (paths["manifest"], manifest),
                (paths["bundle"], source_bundle),
                (paths["ledger"], ledger),
                (paths["notes"], notes),
                (paths["score"], score),
                (paths["probes"], probes),
                (paths["audit"], audit),
            ]:
                write_json(path, payload)
            packet = build_candidate_packet(
                contract=self.contract,
                manifest_path=paths["manifest"],
                source_bundle_path=paths["bundle"],
                search_ledger_path=paths["ledger"],
                agent_notes_path=paths["notes"],
                public_score_path=paths["score"],
                invariant_probes_path=paths["probes"],
                public_audit_path=paths["audit"],
                packet_id="unit-test-candidate",
            )
            packet["artifacts"]["public_score"]["sha256"] = "0" * 64
            errors = validate_packet(packet, self.contract)
        self.assertTrue(any("public_score.sha256" in error for error in errors))

    def test_cli_builds_candidate_packet(self) -> None:
        manifest, ledger, source_bundle = current_manifest_ledger_and_bundle()
        score = public_score()
        probes = run_invariant_probes()
        audit = run_public_audit()
        notes = load_notes_json(ROOT / "templates/agent-notes.example.json")
        manifest["source_bundle"]["bundle_sha256"] = source_bundle["bundle_sha256"]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            manifest_path = temp / "submission.json"
            bundle_path = temp / "submission-bundle.json"
            ledger_path = temp / "search-ledger.json"
            notes_path = temp / "agent-notes.json"
            score_path = temp / "score.json"
            probes_path = temp / "invariant-probes.json"
            audit_path = temp / "public-audit.json"
            packet_path = temp / "candidate-packet.json"
            for path, payload in [
                (manifest_path, manifest),
                (bundle_path, source_bundle),
                (ledger_path, ledger),
                (notes_path, notes),
                (score_path, score),
                (probes_path, probes),
                (audit_path, audit),
            ]:
                write_json(path, payload)

            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/build_candidate_packet.py",
                    "--manifest",
                    str(manifest_path),
                    "--source-bundle",
                    str(bundle_path),
                    "--search-ledger",
                    str(ledger_path),
                    "--agent-notes",
                    str(notes_path),
                    "--public-score",
                    str(score_path),
                    "--invariant-probes",
                    str(probes_path),
                    "--public-audit",
                    str(audit_path),
                    "--output",
                    str(packet_path),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"candidate_ready": true', result.stdout)


if __name__ == "__main__":
    unittest.main()
