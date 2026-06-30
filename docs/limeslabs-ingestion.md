# limeslabs.eu Ingestion

This repo includes candidate-only example data for the future KernelForge page.
The website should validate leaderboard payloads before rendering them.

## Validation Command

```bash
python3 scripts/validate_leaderboard.py --input examples/limeslabs/leaderboard.example.json
```

The validator reads `verifier/replay-contract.json` and enforces the status
rules used by fixed-runner rankings.

Trusted replay outputs should be validated separately before they are converted
into promoted leaderboard entries:

```bash
python3 scripts/validate_replay_result.py --input templates/replay-result.example.json
```

Promotion packets should validate before the website renders any entry as part
of the official fixed-runner frontier:

```bash
python3 scripts/validate_promotion_packet.py --input templates/promotion-packet.example.json
```

## Required Rules

- `local` and `candidate` entries must keep `hidden_geomean_runtime_ms` null.
- `verified`, `promoted`, `replicated`, and `scaled` entries must include a
  numeric `hidden_geomean_runtime_ms`.
- `verified` and later entries must include `replay.trusted_runner`.
- `verified` and later entries must name a known fixed runner track.
- `promoted` and later entries must link a result card.
- `promoted` and later entries must preserve `metrics.correct == true`.
- `scaled` entries must mark `replay.integration_audit` true.
- `promoted` and later entries must have a validated promotion packet binding
  all correctness, tolerance, runner, replay, baseline, result-card, and
  leaderboard artifacts.

Example fixtures must say that they are not official leaderboard data.

## Website Behavior

Candidate entries may be shown as local telemetry, but they must not appear in
official fixed-runner rankings. Official rankings require hidden correctness and
fixed-runner replay evidence from the verifier contract. The promotion packet is
the source of status evidence; the leaderboard entry is a rendered summary for
the website.
