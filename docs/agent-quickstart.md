# Agent Quickstart

This file is for coding agents pointed at KernelForge.

## Mission

Improve one LLM primitive while preserving correctness. Your local timing is
candidate telemetry. Official ranking requires hidden correctness and fixed
runner replay.
Use `public_speedup_vs_reference` only as a local triage signal; fixed runner
replay decides official speed.

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
4. Record correctness, candidate timing, reference timing, speedup, hardware,
   and failure modes.
5. Fill `submission.json` from `templates/submission.json`.
6. Run `python3 scripts/check_submission.py --manifest submission.json --base origin/main`.
7. Keep negative or mixed attempts in notes.
8. Stop when a candidate has a clear method summary and replay rationale.

## Done Criteria

- Public smoke passes with `correct: true`.
- Tests pass.
- JSON templates still parse.
- Submission preflight passes for the completed manifest.
- Numerical risks and hidden-shape assumptions are documented.
- Agent notes list failed variants and local timing variance when available.
