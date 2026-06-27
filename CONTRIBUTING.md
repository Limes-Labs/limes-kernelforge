# Contributing

KernelForge contributions should make one primitive easier to test or replay.

## Candidate Submissions

Candidate submissions may edit only:

- `solution/rmsnorm.py`
- `solution/rope.py`
- `solution/attention.py`
- `solution/kv_decode.py`
- `solution/native/README.md`

Run:

```bash
scripts/run_smoke.sh
python3 -m unittest discover -s tests
```

Open a candidate issue and include public smoke output, local hardware,
numerical risk, and expected hidden-shape failure modes. Do not claim local
timing is an official fixed-runner result.

## Maintainer Changes

Maintainer-only work may update harness, cases, docs, templates, CI, or verifier
contracts. These changes should preserve correctness-first scoring and explain
whether they change public smoke or only launch governance.

## Review Rule

Correctness comes before speed. A faster kernel that fails hidden shapes,
tolerance, or integration audit is a useful negative result, not a promoted
frontier entry.
