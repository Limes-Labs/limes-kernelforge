# Evaluation

KernelForge is correctness-first. A submission that fails tolerance checks has
no speed score.

## Public Smoke Metrics

`score.json` contains:

- `correct`
- `max_abs_error`
- `max_rel_error`
- `public_geomean_runtime_ms`
- `backend`
- `hardware_fingerprint`

Public timing is candidate telemetry. It is useful for local iteration, but it
is not an official leaderboard rank.

## Correctness

The public harness compares editable solution functions against immutable
reference implementations on tiny tensor cases. The future verifier will add
hidden shapes, longer sequences, dtype-specific tolerance, and edge cases.

## Official Ranking

Official ranking minimizes hidden geomean runtime inside a fixed runner track
after correctness passes. Runners must publish:

- hardware and software fingerprint;
- warmup count and timing repetitions;
- median or robust timing rule;
- memory cap;
- tolerance matrix by dtype;
- integration audit result.
