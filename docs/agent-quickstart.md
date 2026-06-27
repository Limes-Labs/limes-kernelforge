# Agent Quickstart

This file is for coding agents pointed at KernelForge.

## Mission

Improve one LLM primitive while preserving correctness. Your local timing is
candidate telemetry. Official ranking requires hidden correctness and fixed
runner replay.

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
4. Record correctness, timing, hardware, and failure modes.
5. Keep negative or mixed attempts in notes.
6. Stop when a candidate has a clear method summary and replay rationale.

## Done Criteria

- Public smoke passes with `correct: true`.
- Tests pass.
- JSON templates still parse.
- Numerical risks and hidden-shape assumptions are documented.
- Agent notes list failed variants and local timing variance when available.
