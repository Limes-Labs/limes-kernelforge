# Launch TODO

- Freeze hidden shape suite.
- Define tolerance matrix by dtype and primitive.
- Define CPU, Apple Silicon/Metal, CUDA, and ROCm runner configurations.
- Keep `verifier/replay-contract.json` synchronized with fixed runner
  definitions.
- Freeze real fixed-runner manifests based on
  `verifier/trusted-runner-manifest.example.json`.
- Require fixed-runner setup manifests to pass
  `scripts/validate_runner_manifest.py --input path/to/trusted-runner-manifest.json`.
- Require fixed-runner outputs to pass
  `scripts/validate_replay_result.py --input path/to/replay-result.json`.
- Require promotion packets to pass
  `scripts/validate_promotion_packet.py --input path/to/promotion-packet.json`
  before any `promoted`, `replicated`, or `scaled` website status.
- Populate trusted-only `hidden_cases/manifest.json` from the public shape in
  `verifier/hidden-manifest.example.json` and require it to pass
  `scripts/validate_hidden_manifest.py --input path/to/hidden_cases/manifest.json`
  before promotion opens.
- Publish warmup, repetition, and median timing policy.
- Freeze per-track baseline records based on `verifier/baseline-record.example.json`.
- Require promoted comparisons to use baseline records that pass
  `scripts/validate_baseline_record.py --input path/to/baseline-record.json`.
- Define memory caps and measurement method.
- Define native extension submission and sandbox rules.
- Add invalid optimization pattern tests.
- Add numerical edge cases such as long vectors, repeated keys, and near-zero
  norms.
- Add mini integration audit.
- Wire `templates/leaderboard-entry.json` into `limeslabs.eu`.
- Reuse `scripts/validate_leaderboard.py` in the `limeslabs.eu` ingestion job.
- Reuse `scripts/validate_promotion_packet.py` in the `limeslabs.eu` promotion
  ingestion job.
