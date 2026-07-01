#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.candidate_packet_guard import build_candidate_packet, dumps_report
from harness.submission_guard import load_json


ROOT = Path(__file__).resolve().parents[1]


def resolve(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a KernelForge local candidate packet.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--source-bundle", required=True)
    parser.add_argument("--search-ledger", required=True)
    parser.add_argument("--agent-notes", required=True)
    parser.add_argument("--public-score", required=True)
    parser.add_argument("--invariant-probes", required=True)
    parser.add_argument("--public-audit", required=True)
    parser.add_argument("--challenge", default="challenge.json")
    parser.add_argument("--packet-id", default="local-candidate")
    parser.add_argument("--output", help="Optional packet JSON output path.")
    args = parser.parse_args()

    contract = load_json(resolve(args.challenge))
    packet = build_candidate_packet(
        contract=contract,
        manifest_path=resolve(args.manifest),
        source_bundle_path=resolve(args.source_bundle),
        search_ledger_path=resolve(args.search_ledger),
        agent_notes_path=resolve(args.agent_notes),
        public_score_path=resolve(args.public_score),
        invariant_probes_path=resolve(args.invariant_probes),
        public_audit_path=resolve(args.public_audit),
        packet_id=args.packet_id,
        root=ROOT,
    )
    if args.output:
        resolve(args.output).write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = {
        "ok": packet.get("candidate_ready") is True,
        "challenge": packet.get("challenge"),
        "packet_id": packet.get("packet_id"),
        "candidate_ready": packet.get("candidate_ready"),
        "output": str(resolve(args.output)) if args.output else None,
        "failed_gates": packet.get("gates", {}).get("failed", []),
        "blocked_gates": packet.get("gates", {}).get("blocked", []),
    }
    print(dumps_report(report), end="")
    return 0 if packet.get("candidate_ready") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
