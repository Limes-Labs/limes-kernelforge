# Submissions

Submit only the editable solution files plus a completed manifest from
`templates/submission.json`.

## Required Fields

- commit SHA;
- changed editable files;
- primitive targets;
- local public smoke metrics, including reference timing and speedup;
- backend and hardware fingerprint;
- source bundle path and `bundle_sha256`;
- native extension build instructions, if any;
- expected numerical or shape failure modes;
- agent notes or ablation report, if agents were used.

## Reproducibility

Every candidate should run:

```bash
scripts/run_smoke.sh
python3 scripts/run_public_audit.py
python3 scripts/check_public_baseline.py --input baselines/public-smoke-baseline.json
```

## Preflight Guard

Before asking for fixed-runner replay, copy `templates/submission.json` to
`submission.json`, fill every placeholder, and run:

```bash
python3 scripts/build_submission_bundle.py --output submission-bundle.json --base origin/main
python3 scripts/validate_submission_bundle.py --input submission-bundle.json
python3 scripts/check_submission.py --manifest submission.json --base origin/main
python3 scripts/validate_local_bundle.py --manifest submission.json --base origin/main
```

The source bundle hashes the editable files selected for replay and refuses
protected paths or symlinks. Copy its `bundle_sha256` into `submission.json`
before running the manifest guard. The guard checks that the git diff only
touches editable files, that `changed_files` exactly matches the checked diff,
that public correctness is true, and that primitive names and public-score
fields are replay-ready. It is an anti-footgun screen, not a hidden-shape
verifier and not a promotion decision. The local bundle validator reruns public
correctness checks and invariant probes, then checks the manifest, source
bundle, and search ledger against those fresh local outputs. It deliberately
skips timing comparisons because timing becomes official only on fixed runners.

Agent-run submissions should also include validated notes:

```bash
python3 scripts/validate_agent_notes.py --input agent-notes.json
```

Agent-run or multi-attempt candidates should also include one local candidate
packet that binds the completed manifest, source bundle, search ledger, agent
notes, public score, invariant probes, and public audit:

```bash
python3 scripts/build_candidate_packet.py --manifest submission.json --source-bundle submission-bundle.json --search-ledger search-ledger.json --agent-notes agent-notes.json --public-score score.json --invariant-probes invariant-probes.json --public-audit public-audit.json --output candidate-packet.json
python3 scripts/validate_candidate_packet.py --input candidate-packet.json
```

This packet is not a fixed-runner result. It is the local evidence bundle
reviewers use before deciding whether a candidate deserves trusted replay.

Requests for `verified`, `promoted`, `replicated`, or `scaled` status must also
include trusted replay evidence that validates locally:

```bash
python3 scripts/validate_replay_result.py --input replay-result.json
```

Native code is allowed only after the native submission rules in
`docs/launch-todo.md` are finalized.
