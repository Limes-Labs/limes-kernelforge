# Submissions

Submit only the editable solution files plus a completed manifest from
`templates/submission.json`.

## Required Fields

- commit SHA;
- changed editable files;
- primitive targets;
- local public smoke metrics, including reference timing and speedup;
- backend and hardware fingerprint;
- native extension build instructions, if any;
- expected numerical or shape failure modes;
- agent notes or ablation report, if agents were used.

## Reproducibility

Every candidate should run:

```bash
scripts/run_smoke.sh
```

Native code is allowed only after the native submission rules in
`docs/launch-todo.md` are finalized.
