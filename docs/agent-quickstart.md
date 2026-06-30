# Agent Quickstart

This file is for coding agents pointed at KernelForge.

## Mission

Improve one LLM primitive while preserving correctness. Your local timing is
candidate telemetry. Official ranking requires hidden correctness and fixed
runner replay.
Use `public_speedup_vs_reference` only as a local triage signal; fixed runner
replay decides official speed.
Use `public_stress_*` fields to catch obvious numerical or masking regressions
before requesting fixed-runner replay.

## Allowed Edits

- `solution/rmsnorm.py`
- `solution/rope.py`
- `solution/attention.py`
- `solution/kv_decode.py`
- `solution/native/README.md`

Do not edit protected paths listed in `challenge.json`.

## Loop

1. Read `RULES.md`, `EVAL.md`, and `docs/no-cheating-protocol.md`.
2. Make one small primitive change.
3. Run `scripts/run_smoke.sh`.
4. Run `python3 scripts/run_public_audit.py`.
5. Record correctness, invariant probe output, public audit output, candidate timing, stress
   diagnostics, reference timing, speedup, hardware, and failure modes.
6. Fill `submission.json` from `templates/submission.json`, including stress
   diagnostics, invariant probe status, and search-ledger validation status.
7. Run `python3 scripts/check_submission.py --manifest submission.json --base origin/main`.
8. Run `python3 scripts/validate_local_bundle.py --manifest submission.json --base origin/main`.
9. Fill agent notes from `templates/agent-notes.example.json`.
10. Run `python3 scripts/validate_agent_notes.py --input templates/agent-notes.example.json`.
11. Fill the search ledger from `templates/search-ledger.example.json`.
12. Run `python3 scripts/validate_search_ledger.py --input templates/search-ledger.example.json`.
13. Keep negative or mixed attempts in notes and the search ledger.
14. Stop when a candidate has a clear method summary and replay rationale.

## Done Criteria

- Public smoke passes with `correct: true`.
- Public audit passes.
- Tests pass.
- JSON templates still parse.
- Submission preflight passes for the completed manifest.
- Local bundle validation passes against freshly rerun correctness checks and probes.
- Agent notes validation passes for the completed notes packet.
- Search ledger validation passes for the completed search packet.
- Numerical risks and hidden-shape assumptions are documented.
- Agent notes list failed variants and local timing variance when available.
