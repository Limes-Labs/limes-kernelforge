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
5. Run `python3 scripts/check_public_baseline.py --input baselines/public-smoke-baseline.json`.
6. Record correctness, invariant probe output, public audit output, candidate
   timing, stress diagnostics, reference timing, speedup, hardware, and failure
   modes.
7. Run `python3 scripts/build_submission_bundle.py --output submission-bundle.json --base origin/main`.
8. Fill `submission.json` from `templates/submission.json`, including stress
   diagnostics, invariant probe status, source-bundle hash, and search-ledger
   validation status.
9. Run `python3 scripts/validate_submission_bundle.py --input submission-bundle.json`.
10. Run `python3 scripts/check_submission.py --manifest submission.json --base origin/main`.
11. Run `python3 scripts/validate_local_bundle.py --manifest submission.json --base origin/main`.
12. Fill agent notes from `templates/agent-notes.example.json`.
13. Run `python3 scripts/validate_agent_notes.py --input templates/agent-notes.example.json`.
14. Fill the search ledger from `templates/search-ledger.example.json`.
15. Run `python3 scripts/validate_search_ledger.py --input templates/search-ledger.example.json`.
16. Build `candidate-packet.json` after writing real local artifact files.
17. Run `python3 scripts/validate_candidate_packet.py --input candidate-packet.json`.
18. Keep negative or mixed attempts in notes and the search ledger.
19. Stop when a candidate has a clear method summary and replay rationale.

## Done Criteria

- Public smoke passes with `correct: true`.
- Public audit passes.
- Public smoke baseline check passes.
- Tests pass.
- JSON templates still parse.
- Submission preflight passes for the completed manifest.
- Source bundle validation passes for the exact editable files selected for replay.
- Local bundle validation passes against freshly rerun correctness checks, probes, source bundle, and search ledger.
- Candidate packet validation passes for the completed local evidence bundle.
- Agent notes validation passes for the completed notes packet.
- Search ledger validation passes for the completed search packet.
- Numerical risks and hidden-shape assumptions are documented.
- Agent notes list failed variants and local timing variance when available.
