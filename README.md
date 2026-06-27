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

Everything under `harness/`, `cases/`, `hidden_cases/`, `leaderboard/`,
`challenge.json`, and generated score files is protected for official runs.

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
- `backend`
- `hardware_fingerprint`

## Official Verifier Contract

The official verifier will run hidden shapes and dtypes. Correctness is required
before timing. Speed is ranked only inside fixed runner tracks: CPU, Apple
Silicon/Metal, CUDA, and ROCm. Promotion requires a mini integration audit so a
microbenchmark win is not treated as an end-to-end improvement.

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
- `docs/`: anti-cheat, promotion, launch, and agent-notes policies.
- `docs/agent-quickstart.md`: short instructions for coding agents.
- `templates/`: submission, result-card, and leaderboard-entry schemas.
- `examples/limeslabs/`: candidate-only fixtures for website development.
- `tests/`: stdlib tests for contract and scorer behavior.

## Contributing

Start with [CONTRIBUTING.md](CONTRIBUTING.md). Agent-driven attempts should also
read [docs/agent-quickstart.md](docs/agent-quickstart.md) before editing the
solution surface.
