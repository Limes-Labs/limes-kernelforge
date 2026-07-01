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

Everything under `harness/`, `baselines/`, `cases/`, `verifier/`,
`hidden_cases/`, `leaderboard/`, `challenge.json`, and generated score files is
protected for official runs.

## Quickstart

Use Python 3.10 or newer. No external packages are required.

```bash
scripts/run_smoke.sh
python3 scripts/run_invariant_probes.py
python3 scripts/run_public_audit.py
python3 scripts/check_public_baseline.py --input baselines/public-smoke-baseline.json
python3 scripts/build_submission_bundle.py --changed-file solution/rmsnorm.py --output submission-bundle.json
python3 scripts/validate_submission_bundle.py --input submission-bundle.json
python3 scripts/validate_candidate_packet.py --input templates/candidate-packet.example.json --schema-only
python3 scripts/validate_search_ledger.py --input templates/search-ledger.example.json
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
- `public_stress_correct`
- `public_stress_case_count`
- `public_stress_geomean_runtime_ms`
- `backend`
- `tolerance`
- `hardware_fingerprint`

The `public_stress_*` fields come from tiny edge cases for near-zero norms,
manual RoPE phases, causal masking, and repeated KV keys. They are still local
candidate telemetry, not official fixed-runner rankings.

## Submission Preflight

Completed candidates should include a filled `submission.json` based on
`templates/submission.json`. Before requesting fixed-runner replay, run:

```bash
python3 scripts/build_submission_bundle.py --output submission-bundle.json --base origin/main
python3 scripts/validate_submission_bundle.py --input submission-bundle.json
python3 scripts/check_submission.py --manifest submission.json --base origin/main
python3 scripts/validate_local_bundle.py --manifest submission.json --base origin/main
```

The source-bundle step hashes only the editable files that will be replayed,
rejects symlinks and protected paths, and writes a canonical `bundle_sha256`.
Copy that digest into `submission.json` before running the manifest guard. The
guard rejects protected-file edits, files outside the editable surface,
placeholder manifest values, missing public-score fields, unknown primitive
names, missing stress diagnostics, failed invariant probes, missing
search-ledger validation, and candidates that are not correct on public smoke.
The local bundle validator then reruns public correctness checks and invariant
probes and checks the filled manifest, source bundle, and search ledger against
the fresh local outputs. It intentionally does not compare local timing fields,
which remain candidate telemetry until fixed-runner replay. Passing preflight
does not imply promotion; it only means the candidate is shaped for review.

For agent or multi-attempt workflows, bundle the local evidence into one
candidate packet before asking for human review:

```bash
python3 scripts/build_candidate_packet.py \
  --manifest submission.json \
  --source-bundle submission-bundle.json \
  --search-ledger search-ledger.json \
  --agent-notes agent-notes.json \
  --public-score score.json \
  --invariant-probes invariant-probes.json \
  --public-audit public-audit.json \
  --output candidate-packet.json
python3 scripts/validate_candidate_packet.py --input candidate-packet.json
```

A local candidate packet is still candidate-only evidence. It records that the
public artifacts are internally consistent; it does not replace hidden
correctness checks, fixed-runner timing, memory-cap review, or integration
audit.

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

Promotion packets bind correctness, fixed-runner timing, runner manifest,
baseline record, replay output, agent notes, result card, and leaderboard entry
into one machine-checkable evidence bundle before any public frontier status is
requested:

```bash
python3 scripts/validate_promotion_packet.py --input templates/promotion-packet.example.json
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
- `harness/invariant_probes.py`: candidate-only public probes for finite
  output, mutation safety, causal prefix invariance, and KV alias handling.
- `harness/public_audit.py`: candidate-only static boundary and metamorphic
  audits for numerical shortcuts that public cases alone may miss.
- `harness/source_bundle_guard.py`: hashes the editable source files selected
  for replay and rejects stale or protected-file bundles.
- `harness/candidate_packet_guard.py`: validates local candidate evidence
  packets before fixed-runner replay is requested.
- `baselines/public-smoke-baseline.json`: stable public smoke contract used to
  detect accidental benchmark drift. It is not an official fixed-runner result.
- `cases/public_smoke/`: tiny public tensor cases and stress cases.
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
- `templates/search-ledger.example.json`: machine-checkable search budget,
  attempt, stopping, and selection accounting.
- `templates/submission-bundle.example.json`: schema-only editable source
  bundle shape for replay packaging.
- `templates/candidate-packet.example.json`: schema-only local candidate packet
  shape for agents and reviewers.
- `templates/replay-result.example.json`: schema-only trusted replay result
  packet.
- `templates/promotion-packet.example.json`: schema-only promotion evidence
  bundle. It is not an official promotion packet.
- `examples/limeslabs/`: candidate-only fixtures for website development.
- `tests/`: stdlib tests for contract and scorer behavior.

## Contributing

Start with [CONTRIBUTING.md](CONTRIBUTING.md). Agent-driven attempts should also
read [docs/agent-quickstart.md](docs/agent-quickstart.md) before editing the
solution surface.
