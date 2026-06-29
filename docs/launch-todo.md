# Launch TODO

- Freeze hidden shape suite.
- Define tolerance matrix by dtype and primitive.
- Define CPU, Apple Silicon/Metal, CUDA, and ROCm runner configurations.
- Keep `verifier/replay-contract.json` synchronized with fixed runner
  definitions.
- Require fixed-runner outputs to pass
  `scripts/validate_replay_result.py --input path/to/replay-result.json`.
- Fill trusted-only `hidden_cases/manifest.json` with shape-suite hashes before
  promotion opens.
- Publish warmup, repetition, and median timing policy.
- Define memory caps and measurement method.
- Define native extension submission and sandbox rules.
- Add invalid optimization pattern tests.
- Add numerical edge cases such as long vectors, repeated keys, and near-zero
  norms.
- Add mini integration audit.
- Wire `templates/leaderboard-entry.json` into `limeslabs.eu`.
- Reuse `scripts/validate_leaderboard.py` in the `limeslabs.eu` ingestion job.
