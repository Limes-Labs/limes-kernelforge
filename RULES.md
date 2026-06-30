# Rules

Limes KernelForge is a kernel arena. It rewards correct, replayable primitive
improvements, not edits to the benchmark harness or hardware-only advantages.

## Editable Paths

Official submissions may edit only:

- `solution/rmsnorm.py`
- `solution/rope.py`
- `solution/attention.py`
- `solution/kv_decode.py`
- `solution/native/README.md`

## Forbidden Paths

Official submissions must not edit:

- `harness/**`
- `cases/**`
- `verifier/**`
- `hidden_cases/**`
- `challenge.json`
- `score.json`
- `leaderboard/**`

The same forbidden paths are listed in `challenge.json`.

The local preflight guard can catch most accidental contract violations before
review:

```bash
python3 scripts/check_submission.py --manifest submission.json --base origin/main
python3 scripts/validate_local_bundle.py --manifest submission.json --base origin/main
```

## Prohibited Behavior

- Changing public or hidden tensor cases.
- Changing the reference harness, verifier specs, tolerances, timing policy, or
  challenge contract.
- Claiming a local timing as an official fixed-runner result.
- Downloading code, models, data, or remote services during official scoring.
- Returning approximations outside tolerance to win speed.
- Special-casing public tensor values instead of implementing the primitive.

## Tracks

- `public-smoke`: dependency-free local correctness and telemetry.
- `cpu-fixed`: official CPU runner.
- `apple-metal-fixed`: official Apple Silicon/Metal runner.
- `cuda-fixed`: official CUDA runner.
- `rocm-fixed`: official ROCm runner.
- `integration-audit`: replay inside a mini inference or training loop.
