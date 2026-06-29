# Evaluation

KernelForge is correctness-first. A submission that fails tolerance checks has
no speed score.
The public machine-readable verifier contract is
`verifier/replay-contract.json`.

## Public Smoke Metrics

`score.json` contains:

- `correct`
- `max_abs_error`
- `max_rel_error`
- `public_geomean_runtime_ms`
- `reference_public_geomean_runtime_ms`
- `public_runtime_delta_ms`
- `public_speedup_vs_reference`
- `backend`
- `tolerance`
- `hardware_fingerprint`

Public timing is candidate telemetry. It is useful for local iteration, but it
is not an official leaderboard rank. The reference timing is measured on the
same local run against the immutable stdlib reference implementation so agents
can distinguish likely algorithmic progress from ordinary timing noise. Fixed
runner replay still decides official ranking.

## Correctness

The public harness compares editable solution functions against immutable
reference implementations on tiny tensor cases. The future verifier will add
hidden shapes, longer sequences, dtype-specific tolerance, and edge cases.

## Official Ranking

Official ranking minimizes hidden geomean runtime inside a fixed runner track
after correctness passes. `public_geomean_runtime_ms` is a public metric for
candidate selection; `hidden_geomean_runtime_ms` is the official primary metric.
Runners must publish:

- hardware and software fingerprint;
- warmup count and timing repetitions;
- median or robust timing rule;
- memory cap;
- tolerance matrix by dtype;
- integration audit result.

The public repository intentionally sets `hidden_verifier_ready` to `false` in
the replay contract until hidden cases, runner manifests, lockfiles, and fixed
hardware definitions exist outside the public repo.
