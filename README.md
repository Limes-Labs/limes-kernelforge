# Limes KernelForge

Limes KernelForge is a correctness-first LLM kernel optimization challenge.
Participants edit small primitive implementations while the reference harness,
public tensor cases, challenge contract, and future hidden cases stay fixed.

Public smoke timings are local candidate telemetry. Official speed rankings
require fixed runner tracks, hidden tensor shapes, numerical tolerance checks,
and an integration audit inside a mini inference or training loop.

## Initial Primitives

- RMSNorm
- RoPE
- causal attention prefill
- KV decode microcase

## What You Can Edit

- `solution/rmsnorm.py`
- `solution/rope.py`
- `solution/attention.py`
- `solution/kv_decode.py`
- `solution/native/README.md` for future CUDA, Triton, Metal, HIP, or SIMD
  extension notes.

Everything under `harness/`, `cases/`, `verifier/`, `hidden_cases/`,
`leaderboard/`, `challenge.json`, and generated score files is protected for
official runs.

## Quickstart

Use Python 3.10 or newer. No external packages are required.

```bash
scripts/run_smoke.sh
python3 -m unittest discover -s tests
python3 -m json.tool challenge.json
```

The smoke run compares editable solution functions against immutable reference
implementations on tiny public cases and writes `score.json` with:

- `correct`
- `max_abs_error`
- `max_rel_error`
- `public_geomean_runtime_ms`
- `reference_public_geomean_runtime_ms`
- `public_speedup_vs_reference`
- `backend`
- `tolerance`
- `hardware_fingerprint`

## Submission Preflight

Completed candidates should include a filled `submission.json` based on
`templates/submission.json`. Before requesting fixed-runner replay, run:

```bash
python3 scripts/check_submission.py --manifest submission.json --base origin/main
```

The guard rejects protected-file edits, files outside the editable surface,
placeholder manifest values, missing public-score fields, unknown primitive
names, and candidates that are not correct on public smoke. Passing preflight
does not imply promotion; it only means the candidate is shaped for review.

## Official Verifier Contract

The official verifier will run hidden shapes and dtypes. Correctness is required
before timing. Speed is ranked only inside fixed runner tracks: CPU, Apple
Silicon/Metal, CUDA, and ROCm. Promotion requires a mini integration audit so a
microbenchmark win is not treated as an end-to-end improvement.

The machine-readable public verifier contract lives at
`verifier/replay-contract.json`. Trusted runners can inspect the same contract
through:

```bash
python3 harness/verify_hidden.py --public-contract-only
```

Trusted runner outputs should validate before any website ingestion or status
promotion:

```bash
python3 scripts/validate_replay_result.py --input templates/replay-result.example.json
```

Trusted runner setups should also validate their public manifest shape before
promotion opens:

```bash
python3 scripts/validate_runner_manifest.py --input verifier/trusted-runner-manifest.example.json
```

Locked baseline records should validate before promoted comparisons are allowed:

```bash
python3 scripts/validate_baseline_record.py --input verifier/baseline-record.example.json
```

## Status Labels

```text
local -> candidate -> verified -> promoted -> replicated -> scaled
```

Local timings are not public frontier claims.

## Repository Map

- `challenge.json`: Benchforge-style challenge contract.
- `solution/`: editable participant surface.
- `harness/`: immutable public reference and scoring code.
- `cases/public_smoke/`: tiny public tensor cases.
- `verifier/replay-contract.json`: public fixed-runner, promotion, and
  ingestion contract. It does not include hidden cases.
- `verifier/task-spec.json`: public primitive and hidden replay-axis
  specification. It does not include hidden cases.
- `verifier/trusted-runner-manifest.example.json`: schema-only fixed-runner
  setup manifest. It does not include hidden cases.
- `verifier/baseline-record.example.json`: schema-only reference baseline
  record. It is not an official comparison baseline.
- `docs/`: anti-cheat, promotion, launch, and agent-notes policies.
- `docs/verifier-runbook.md`: trusted-runner replay checklist.
- `docs/limeslabs-ingestion.md`: website ingestion and status validation rules.
- `docs/agent-quickstart.md`: short instructions for coding agents.
- `templates/`: submission, result-card, and leaderboard-entry schemas.
- `templates/agent-notes.example.json`: machine-checkable agent trial notes.
- `templates/replay-result.example.json`: schema-only trusted replay result
  packet.
- `examples/limeslabs/`: candidate-only fixtures for website development.
- `tests/`: stdlib tests for contract and scorer behavior.

## Contributing

Start with [CONTRIBUTING.md](CONTRIBUTING.md). Agent-driven attempts should also
read [docs/agent-quickstart.md](docs/agent-quickstart.md) before editing the
solution surface.
