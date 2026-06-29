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

## Preflight Guard

Before asking for fixed-runner replay, copy `templates/submission.json` to
`submission.json`, fill every placeholder, and run:

```bash
python3 scripts/check_submission.py --manifest submission.json --base origin/main
```

The guard checks that the git diff only touches editable files, that
`changed_files` exactly matches the checked diff, that public correctness is
true, and that primitive names and public-score fields are replay-ready. It is
an anti-footgun screen, not a hidden-shape verifier and not a promotion
decision.

Native code is allowed only after the native submission rules in
`docs/launch-todo.md` are finalized.
