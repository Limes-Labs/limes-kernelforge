# limeslabs.eu Fixtures

These files are static examples for building the future `limeslabs.eu`
KernelForge page. They are not official leaderboard data.

Use them to render:

- a candidate-only public smoke row;
- a result-card link;
- the local/candidate/verified/promoted/replicated/scaled status language.

Rules for website prototypes:

- show `public_geomean_runtime_ms` as local candidate telemetry;
- show `reference_public_geomean_runtime_ms` and
  `public_speedup_vs_reference` as local reference-comparison fields;
- keep `hidden_geomean_runtime_ms` null until fixed-runner replay exists;
- do not render candidate examples as official runner records;
- link back to the repository and result card for provenance.

Validate fixture payloads with:

```bash
python3 scripts/validate_leaderboard.py --input examples/limeslabs/leaderboard.example.json
```
