# No-Cheating Protocol

## Frozen Question

- Objective: improve LLM primitive runtime without changing the mathematical
  result beyond tolerance.
- Public metric: `public_geomean_runtime_ms`.
- Public stress diagnostics: `public_stress_*` fields.
- Official metric: `hidden_geomean_runtime_ms` inside fixed runner tracks.
- Direction: lower is better after correctness passes.

## Boundaries

- Public cases and public stress cases are for interface validation and
  falsification diagnostics.
- Public invariant probes are deterministic interface checks only; passing them
  is not fixed-runner evidence.
- Hidden cases and fixed-runner results may not influence candidate selection.
- Official scoring runs with no network access.

## Promotion Gate

Promote only if:

- hidden correctness passes;
- fixed-runner timing improves over baseline;
- memory cap is respected;
- integration audit does not regress;
- replay results are recorded with hardware and software fingerprints.

Search-ledger packets should validate with
`python3 scripts/validate_search_ledger.py --input path/to/search-ledger.json`
before fixed-runner replay is requested.

Trusted replay requests must validate with
`python3 scripts/validate_replay_request.py --input path/to/replay-request.json`.
The request must freeze the candidate, bind the local candidate packet, declare
the fixed runner track, stay within replay quotas, and explicitly reject hidden
or fixed-runner feedback for candidate selection.

Mark as `negative` or `mixed` when a kernel wins a public microcase but fails
hidden shapes, tolerance, or integration audit.
